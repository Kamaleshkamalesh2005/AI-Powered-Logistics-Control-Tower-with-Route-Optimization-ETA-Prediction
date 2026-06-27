from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import sys
from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings
from app.models import Base  # noqa: F401
import app.models  # noqa: F401

TABLE_LOAD_ORDER = ["vehicles", "drivers", "trips", "shipments", "route_stops", "delay_events"]

CSV_SPECS: dict[str, dict[str, list[str]]] = {
    "vehicles.csv": {"parse_dates": []},
    "drivers.csv": {"parse_dates": ["license_expiry"]},
    "trips.csv": {"parse_dates": ["planned_departure_at", "planned_arrival_at", "actual_departure_at", "actual_arrival_at"]},
    "shipments.csv": {"parse_dates": ["eta", "planned_pickup_at", "planned_delivery_at", "actual_delivery_at"]},
    "route_stops.csv": {"parse_dates": ["planned_arrival_at", "actual_arrival_at"]},
    "delay_events.csv": {"parse_dates": ["occurred_at", "resolved_at"]},
}

DATE_ONLY_COLUMNS = {
    "drivers.csv": {"license_expiry"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bulk load synthetic logistics data into Postgres.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=BACKEND_ROOT / "data" / "synthetic",
        help="Directory containing the generated CSV files.",
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=settings.database_url,
        help="SQLAlchemy async database URL. Defaults to DATABASE_URL from backend settings.",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Truncate target tables before loading data.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing CSV file: {path}")
    spec = CSV_SPECS.get(path.name, {})
    return pd.read_csv(path, parse_dates=spec.get("parse_dates", []))


def normalize_records(dataframe: pd.DataFrame, *, table_name: str, source_name: str) -> list[dict[str, Any]]:
    sanitized = dataframe.where(pd.notna(dataframe), None)
    allowed_columns = set(Base.metadata.tables[table_name].columns.keys())
    date_only_columns = DATE_ONLY_COLUMNS.get(source_name, set())
    records: list[dict[str, Any]] = []
    for raw_row in sanitized.to_dict(orient="records"):
        row: dict[str, Any] = {}
        for column_name in allowed_columns:
            value = raw_row.get(column_name)
            if value is None:
                row[column_name] = None
            elif column_name in date_only_columns:
                row[column_name] = pd.Timestamp(value).date()
            elif isinstance(value, pd.Timestamp):
                row[column_name] = value.to_pydatetime()
            else:
                row[column_name] = value
        records.append(row)
    return records


def chunked(values: list[dict[str, Any]], size: int = 500) -> list[list[dict[str, Any]]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


async def load_dataset(database_url: str, data_dir: Path, truncate: bool) -> None:
    engine = create_async_engine(database_url, echo=False, pool_pre_ping=True)

    shipments = normalize_records(read_csv(data_dir / "shipments.csv"), table_name="shipments", source_name="shipments.csv")
    trips = normalize_records(read_csv(data_dir / "trips.csv"), table_name="trips", source_name="trips.csv")
    route_stops = normalize_records(read_csv(data_dir / "route_stops.csv"), table_name="route_stops", source_name="route_stops.csv")
    delay_events = normalize_records(read_csv(data_dir / "delay_events.csv"), table_name="delay_events", source_name="delay_events.csv")
    vehicles = normalize_records(read_csv(data_dir / "vehicles.csv"), table_name="vehicles", source_name="vehicles.csv")
    drivers = normalize_records(read_csv(data_dir / "drivers.csv"), table_name="drivers", source_name="drivers.csv")

    async with engine.begin() as connection:
        if truncate:
            await connection.execute(
                text(
                    "TRUNCATE TABLE delay_events, route_stops, shipments, trips, drivers, vehicles RESTART IDENTITY CASCADE"
                )
            )

        for table_name, records in [
            ("vehicles", vehicles),
            ("drivers", drivers),
            ("trips", trips),
            ("shipments", shipments),
            ("route_stops", route_stops),
            ("delay_events", delay_events),
        ]:
            table = Base.metadata.tables[table_name]
            for batch in chunked(records):
                await connection.execute(table.insert(), batch)

    await engine.dispose()


def main() -> None:
    args = parse_args()
    asyncio.run(load_dataset(args.database_url, args.data_dir, args.truncate))
    print(f"Loaded synthetic logistics data from {args.data_dir}")


if __name__ == "__main__":
    main()
