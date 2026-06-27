from __future__ import annotations

import argparse
from datetime import datetime
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
import os
import sys
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings

IST = ZoneInfo("Asia/Kolkata")
VEHICLE_TYPE_MAP = {
    ("tata", "ace ev"): "tata_ace_ev",
    ("ashok leyland", "bada dost"): "ashok_leyland_bada_dost",
    ("mahindra", "bolero pik-up"): "mahindra_bolero_pik_up",
    ("eicher", "pro 2059"): "eicher_pro_2059",
    ("volvo", "fmx"): "volvo_fmx",
}
WEATHER_STATES = {
    "Delhi": "foggy",
    "Delhi NCR": "foggy",
    "Jaipur": "hot",
    "Ahmedabad": "hot",
    "Surat": "rainy",
    "Mumbai": "rainy",
    "Pune": "rainy",
    "Bengaluru": "clear",
    "Chennai": "hazy",
    "Hyderabad": "hot",
    "Kolkata": "foggy",
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    a = sin(delta_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(delta_lon / 2) ** 2
    return 2 * earth_radius_km * asin(sqrt(a))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train an XGBoost ETA regression model from synthetic logistics data.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=BACKEND_ROOT / "data" / "synthetic",
        help="Directory containing the synthetic CSV files from Phase 3.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=BACKEND_ROOT / settings.eta_model_path,
        help="Path where the trained joblib artifact will be saved.",
    )
    return parser.parse_args()


def load_dataset(data_dir: Path) -> pd.DataFrame:
    shipments_path = data_dir / "shipments.csv"
    trips_path = data_dir / "trips.csv"
    vehicles_path = data_dir / "vehicles.csv"

    if not shipments_path.exists() or not trips_path.exists() or not vehicles_path.exists():
        raise FileNotFoundError(
            f"Expected shipments.csv, trips.csv, and vehicles.csv under {data_dir}. Run the Phase 3 synthetic data generator first."
        )

    shipments = pd.read_csv(shipments_path)
    trips = pd.read_csv(trips_path)
    vehicles = pd.read_csv(vehicles_path)

    shipments["planned_pickup_at"] = pd.to_datetime(shipments["planned_pickup_at"], utc=False, errors="coerce")
    shipments["planned_delivery_at"] = pd.to_datetime(shipments["planned_delivery_at"], utc=False, errors="coerce")
    shipments["actual_delivery_at"] = pd.to_datetime(shipments["actual_delivery_at"], utc=False, errors="coerce")
    trips["planned_departure_at"] = pd.to_datetime(trips["planned_departure_at"], utc=False, errors="coerce")
    trips["planned_arrival_at"] = pd.to_datetime(trips["planned_arrival_at"], utc=False, errors="coerce")

    merged = shipments.merge(
        trips[["id", "fuel_cost_inr", "planned_departure_at", "planned_arrival_at", "actual_arrival_at"]],
        left_on="trip_id",
        right_on="id",
        how="left",
        suffixes=("", "_trip"),
    ).merge(
        vehicles[["id", "make", "model"]],
        left_on="vehicle_id",
        right_on="id",
        how="left",
        suffixes=("", "_vehicle"),
    )

    merged = merged.dropna(subset=["planned_pickup_at", "planned_delivery_at", "actual_delivery_at", "distance_km", "make", "model"])
    merged = merged.copy()
    merged["actual_delivery_at"] = pd.to_datetime(merged["actual_delivery_at"], errors="coerce")
    merged["planned_pickup_at"] = pd.to_datetime(merged["planned_pickup_at"], errors="coerce")
    merged["planned_delivery_at"] = pd.to_datetime(merged["planned_delivery_at"], errors="coerce")
    merged = merged.dropna(subset=["actual_delivery_at", "planned_pickup_at", "planned_delivery_at"])

    merged["vehicle_type"] = merged.apply(
        lambda row: map_vehicle_type(str(row["make"]), str(row["model"])),
        axis=1,
    )
    merged["time_of_day"] = merged["planned_pickup_at"].apply(time_of_day_from_timestamp)
    merged["day_of_week"] = merged["planned_pickup_at"].dt.dayofweek.astype(int)
    merged["weather_condition"] = merged.apply(derive_weather_condition, axis=1)
    merged["route_key"] = merged["origin"].astype(str) + "|" + merged["destination"].astype(str)
    merged = merged.sort_values("planned_pickup_at")
    merged["delay_minutes"] = (
        merged["actual_delivery_at"] - merged["planned_delivery_at"]
    ).dt.total_seconds().div(60.0).clip(lower=0.0)
    merged["historical_avg_delay_for_route"] = merged.groupby("route_key", group_keys=False)["delay_minutes"].transform(
        lambda values: values.shift(1).expanding().mean()
    )
    merged["historical_avg_delay_for_route"] = merged["historical_avg_delay_for_route"].fillna(merged["delay_minutes"].median())
    merged["eta_minutes"] = (
        merged["actual_delivery_at"] - merged["planned_pickup_at"]
    ).dt.total_seconds().div(60.0)

    return merged


def map_vehicle_type(make: str, model: str) -> str:
    key = (make.strip().lower(), model.strip().lower())
    if key in VEHICLE_TYPE_MAP:
        return VEHICLE_TYPE_MAP[key]
    return "eicher_pro_2059"


def time_of_day_from_timestamp(timestamp: pd.Timestamp) -> str:
    hour = int(timestamp.hour)
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 21:
        return "evening"
    return "night"


def derive_weather_condition(row: pd.Series) -> str:
    origin_city = str(row.get("origin", ""))
    timestamp = row["planned_pickup_at"]
    month = int(timestamp.month)
    base_weather = WEATHER_STATES.get(origin_city, "clear")

    if month in {12, 1} and origin_city in {"Delhi", "Jaipur", "Kolkata"}:
        return "foggy"
    if month in {6, 7, 8, 9} and origin_city in {"Mumbai", "Pune", "Surat", "Chennai"}:
        return "rainy"
    if month in {4, 5, 6}:
        return "hot"
    return base_weather


def build_feature_frame(dataframe: pd.DataFrame) -> pd.DataFrame:
    return dataframe[
        [
            "distance_km",
            "vehicle_type",
            "time_of_day",
            "day_of_week",
            "historical_avg_delay_for_route",
            "weather_condition",
        ]
    ].copy()


def train_model(data_dir: Path, output_path: Path) -> dict[str, float | str | int]:
    dataset = load_dataset(data_dir)

    feature_frame = build_feature_frame(dataset)
    target = dataset["eta_minutes"].astype(float)

    x_train, x_test, y_train, y_test = train_test_split(feature_frame, target, test_size=0.2, random_state=42)

    numeric_features = ["distance_km", "day_of_week", "historical_avg_delay_for_route"]
    categorical_features = ["vehicle_type", "time_of_day", "weather_condition"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median"))]), numeric_features),
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_features,
            ),
        ]
    )

    model = XGBRegressor(
        objective="reg:squarederror",
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=max((os.cpu_count() or 1) - 1, 1),
    )

    pipeline = Pipeline([("preprocessor", preprocessor), ("model", model)])
    pipeline.fit(x_train, y_train)

    predictions = pipeline.predict(x_test)
    mae = mean_absolute_error(y_test, predictions)
    rmse = mean_squared_error(y_test, predictions, squared=False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    artifact = {
        "model": pipeline,
        "trained_at": datetime.now(IST).isoformat(),
        "metrics": {"mae": float(mae), "rmse": float(rmse)},
        "feature_columns": list(feature_frame.columns),
        "target_column": "eta_minutes",
        "training_rows": int(len(dataset)),
    }
    joblib.dump(artifact, output_path)

    metrics_path = output_path.with_suffix(".metrics.json")
    metrics_path.write_text(
        pd.Series(
            {
                "mae": round(float(mae), 4),
                "rmse": round(float(rmse), 4),
                "training_rows": int(len(dataset)),
                "artifacts": str(output_path),
            }
        ).to_json(indent=2),
        encoding="utf-8",
    )

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "training_rows": int(len(dataset)),
        "output_path": str(output_path),
    }


def main() -> None:
    args = parse_args()
    results = train_model(args.data_dir, args.output_path)
    print(
        "ETA model trained successfully: "
        f"MAE={results['mae']:.2f} min, RMSE={results['rmse']:.2f} min, rows={results['training_rows']}"
    )
    print(f"Saved model to {results['output_path']}")


if __name__ == "__main__":
    main()
