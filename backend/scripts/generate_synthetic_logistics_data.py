from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
import random
import sys
from zoneinfo import ZoneInfo

import pandas as pd
from faker import Faker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.models.enums import DelaySeverity, DriverStatus, RouteStopStatus, ShipmentStatus, TripStatus, VehicleStatus

IST = ZoneInfo("Asia/Kolkata")
SEED = 42
OUTPUT_DIR = BACKEND_ROOT / "data" / "synthetic"

fake = Faker("en_IN")
rng = random.Random(SEED)
Faker.seed(SEED)


@dataclass(frozen=True)
class City:
    name: str
    state: str
    latitude: float
    longitude: float


CITIES: list[City] = [
    City("Delhi", "Delhi", 28.6139, 77.2090),
    City("Mumbai", "Maharashtra", 19.0760, 72.8777),
    City("Bengaluru", "Karnataka", 12.9716, 77.5946),
    City("Chennai", "Tamil Nadu", 13.0827, 80.2707),
    City("Kolkata", "West Bengal", 22.5726, 88.3639),
    City("Hyderabad", "Telangana", 17.3850, 78.4867),
    City("Pune", "Maharashtra", 18.5204, 73.8567),
    City("Ahmedabad", "Gujarat", 23.0225, 72.5714),
    City("Jaipur", "Rajasthan", 26.9124, 75.7873),
    City("Surat", "Gujarat", 21.1702, 72.8311),
]

VEHICLE_MAKES = [
    ("Tata", "Ace EV"),
    ("Ashok Leyland", "Bada Dost"),
    ("Mahindra", "Bolero Pik-Up"),
    ("Eicher", "Pro 2059"),
    ("Volvo", "FMX"),
]

REASON_CODES = [
    "traffic",
    "weather",
    "loading_delay",
    "customs_hold",
    "vehicle_breakdown",
    "crew_change",
]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return 2 * earth_radius_km * asin(sqrt(a))


def jitter_coordinates(city: City, spread: float = 0.08) -> tuple[float, float]:
    return (
        round(city.latitude + rng.uniform(-spread, spread), 7),
        round(city.longitude + rng.uniform(-spread, spread), 7),
    )


def random_plate(index: int) -> str:
    state_code = rng.choice(["DL", "MH", "KA", "TN", "WB", "TG", "GJ", "RJ"])
    district_code = f"{rng.randint(1, 99):02d}"
    series = f"{rng.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}{rng.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}"
    suffix = f"{1000 + index:04d}"
    return f"{state_code}-{district_code}-{series}-{suffix}"


def generate_vin(index: int) -> str:
    alphabet = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"
    prefix = "MAT"
    body = "".join(rng.choice(alphabet) for _ in range(13))
    return f"{prefix}{body}{index % 10}"


def city_pair() -> tuple[City, City]:
    origin = rng.choice(CITIES)
    destination = rng.choice([city for city in CITIES if city != origin])
    return origin, destination


def random_departure_window() -> datetime:
    now = datetime.now(IST)
    return now - timedelta(days=rng.randint(0, 120), hours=rng.randint(0, 23), minutes=rng.randint(0, 59))


def build_vehicle_rows() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for vehicle_id in range(1, 51):
        city = CITIES[(vehicle_id - 1) % len(CITIES)]
        make, model = VEHICLE_MAKES[(vehicle_id - 1) % len(VEHICLE_MAKES)]
        rows.append(
            {
                "id": vehicle_id,
                "fleet_number": f"FL-{vehicle_id:04d}",
                "license_plate": random_plate(vehicle_id),
                "vin": generate_vin(vehicle_id),
                "make": make,
                "model": model,
                "year": rng.randint(2018, 2025),
                "capacity_kg": round(rng.uniform(1500, 14000), 2),
                "status": rng.choices(
                    [VehicleStatus.AVAILABLE.value, VehicleStatus.IN_TRANSIT.value, VehicleStatus.MAINTENANCE.value, VehicleStatus.OFFLINE.value],
                    weights=[0.55, 0.2, 0.15, 0.1],
                    k=1,
                )[0],
                "home_city": city.name,
                "home_state": city.state,
                "home_latitude": city.latitude,
                "home_longitude": city.longitude,
                "notes": fake.sentence(nb_words=8),
            }
        )
    return pd.DataFrame(rows)


def build_driver_rows() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for driver_id in range(1, 31):
        city = CITIES[(driver_id + 2) % len(CITIES)]
        first_name = fake.first_name()
        last_name = fake.last_name()
        rows.append(
            {
                "id": driver_id,
                "employee_code": f"DRV-{driver_id:04d}",
                "first_name": first_name,
                "last_name": last_name,
                "email": fake.unique.email(),
                "phone_number": f"+91-{rng.randint(7000000000, 9999999999)}",
                "license_number": f"DL-{rng.randint(10, 99)}-{rng.randint(100000, 999999)}-{driver_id:04d}",
                "license_expiry": (datetime.now(IST).date() + timedelta(days=rng.randint(180, 1800))).isoformat(),
                "home_base": city.name,
                "status": rng.choices(
                    [DriverStatus.ACTIVE.value, DriverStatus.INACTIVE.value, DriverStatus.ON_LEAVE.value],
                    weights=[0.78, 0.12, 0.1],
                    k=1,
                )[0],
                "user_id": None,
                "notes": fake.sentence(nb_words=8),
            }
        )
    return pd.DataFrame(rows)


def build_shipment_trip_route_rows() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    shipment_rows: list[dict[str, object]] = []
    trip_rows: list[dict[str, object]] = []
    route_stop_rows: list[dict[str, object]] = []
    delay_event_rows: list[dict[str, object]] = []

    vehicle_ids = list(range(1, 51))
    driver_ids = list(range(1, 31))
    delay_event_id = 1

    shipment_status_choices = [
        ShipmentStatus.DELIVERED.value,
        ShipmentStatus.IN_TRANSIT.value,
        ShipmentStatus.EXCEPTION.value,
        ShipmentStatus.PLANNED.value,
    ]
    shipment_weights = [0.78, 0.1, 0.07, 0.05]

    trip_status_choices = [
        TripStatus.COMPLETED.value,
        TripStatus.IN_PROGRESS.value,
        TripStatus.DELAYED.value,
        TripStatus.PLANNED.value,
        TripStatus.CANCELLED.value,
    ]
    trip_weights = [0.74, 0.12, 0.08, 0.04, 0.02]

    for shipment_id in range(1, 2001):
        origin, destination = city_pair()
        vehicle_id = rng.choice(vehicle_ids)
        driver_id = rng.choice(driver_ids)
        trip_departure = random_departure_window()
        distance_km = haversine_km(origin.latitude, origin.longitude, destination.latitude, destination.longitude)
        travel_hours = max(distance_km / rng.uniform(38.0, 55.0), 3.0)
        planned_arrival = trip_departure + timedelta(hours=travel_hours)
        actual_departure = trip_departure + timedelta(minutes=rng.randint(0, 30))

        delay_flag = rng.random() < min(0.32, 0.08 + (distance_km / 2500.0))
        delay_minutes = 0
        if delay_flag:
            delay_minutes = rng.randint(20, 240)

        actual_arrival = planned_arrival + timedelta(minutes=delay_minutes)
        fuel_cost = round(distance_km * rng.uniform(7.5, 11.5), 2)
        shipment_status = rng.choices(shipment_status_choices, weights=shipment_weights, k=1)[0]
        trip_status = rng.choices(trip_status_choices, weights=trip_weights, k=1)[0]
        if delay_flag and shipment_status == ShipmentStatus.DELIVERED.value:
            trip_status = TripStatus.DELAYED.value

        eta = actual_arrival if shipment_status == ShipmentStatus.DELIVERED.value else planned_arrival
        route_name = f"{origin.name} to {destination.name} corridor"
        origin_latitude, origin_longitude = jitter_coordinates(origin)
        destination_latitude, destination_longitude = jitter_coordinates(destination)

        trip_rows.append(
            {
                "id": shipment_id,
                "trip_number": f"TRP-{shipment_id:06d}",
                "route_name": route_name,
                "status": trip_status,
                "planned_departure_at": trip_departure.isoformat(),
                "planned_arrival_at": planned_arrival.isoformat(),
                "actual_departure_at": actual_departure.isoformat() if trip_status != TripStatus.PLANNED.value else None,
                "actual_arrival_at": actual_arrival.isoformat() if shipment_status != ShipmentStatus.IN_TRANSIT.value else None,
                "fuel_cost_inr": fuel_cost,
                "notes": f"Synthetic {route_name} movement.",
                "vehicle_id": vehicle_id,
                "driver_id": driver_id,
                "created_by_user_id": None,
            }
        )

        shipment_rows.append(
            {
                "id": shipment_id,
                "reference": f"SHP-{shipment_id:07d}",
                "origin": origin.name,
                "destination": destination.name,
                "customer_name": fake.company(),
                "status": shipment_status,
                "eta": eta.isoformat(),
                "planned_pickup_at": trip_departure.isoformat(),
                "planned_delivery_at": planned_arrival.isoformat(),
                "actual_delivery_at": actual_arrival.isoformat() if shipment_status == ShipmentStatus.DELIVERED.value else None,
                "notes": fake.sentence(nb_words=10),
                "vehicle_id": vehicle_id,
                "driver_id": driver_id,
                "trip_id": shipment_id,
                "created_by_user_id": None,
                "origin_city": origin.name,
                "origin_state": origin.state,
                "origin_latitude": origin_latitude,
                "origin_longitude": origin_longitude,
                "destination_city": destination.name,
                "destination_state": destination.state,
                "destination_latitude": destination_latitude,
                "destination_longitude": destination_longitude,
                "distance_km": round(distance_km, 2),
                "fuel_cost_inr": fuel_cost,
                "delay_flag": delay_flag,
                "delay_minutes": delay_minutes,
            }
        )

        origin_stop_id = shipment_id * 2 - 1
        destination_stop_id = shipment_id * 2
        route_stop_rows.extend(
            [
                {
                    "id": origin_stop_id,
                    "trip_id": shipment_id,
                    "stop_sequence": 1,
                    "location_name": origin.name,
                    "address": fake.address().replace("\n", ", "),
                    "latitude": origin_latitude,
                    "longitude": origin_longitude,
                    "planned_arrival_at": trip_departure.isoformat(),
                    "actual_arrival_at": actual_departure.isoformat(),
                    "status": RouteStopStatus.COMPLETED.value if trip_status != TripStatus.PLANNED.value else RouteStopStatus.PENDING.value,
                    "notes": "Origin loading point.",
                },
                {
                    "id": destination_stop_id,
                    "trip_id": shipment_id,
                    "stop_sequence": 2,
                    "location_name": destination.name,
                    "address": fake.address().replace("\n", ", "),
                    "latitude": destination_latitude,
                    "longitude": destination_longitude,
                    "planned_arrival_at": planned_arrival.isoformat(),
                    "actual_arrival_at": actual_arrival.isoformat() if shipment_status != ShipmentStatus.IN_TRANSIT.value else None,
                    "status": RouteStopStatus.DELAYED.value if delay_flag else RouteStopStatus.COMPLETED.value,
                    "notes": "Delivery point.",
                },
            ]
        )

        if delay_flag:
            severity = (
                DelaySeverity.CRITICAL.value
                if delay_minutes >= 180
                else DelaySeverity.HIGH.value
                if delay_minutes >= 90
                else DelaySeverity.MEDIUM.value
                if delay_minutes >= 45
                else DelaySeverity.LOW.value
            )
            delay_event_rows.append(
                {
                    "id": delay_event_id,
                    "trip_id": shipment_id,
                    "shipment_id": shipment_id,
                    "route_stop_id": destination_stop_id,
                    "reported_by_user_id": None,
                    "severity": severity,
                    "delay_minutes": delay_minutes,
                    "reason_code": rng.choice(REASON_CODES),
                    "description": fake.sentence(nb_words=12),
                    "occurred_at": (planned_arrival + timedelta(minutes=5)).isoformat(),
                    "resolved_at": actual_arrival.isoformat() if shipment_status == ShipmentStatus.DELIVERED.value else None,
                }
            )
            delay_event_id += 1

    shipments = pd.DataFrame(shipment_rows)
    trips = pd.DataFrame(trip_rows)
    route_stops = pd.DataFrame(route_stop_rows)
    delay_events = pd.DataFrame(delay_event_rows)
    return shipments, trips, route_stops, delay_events


def build_city_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "name": city.name,
                "state": city.state,
                "latitude": city.latitude,
                "longitude": city.longitude,
            }
            for city in CITIES
        ]
    )


def write_csvs(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    build_city_rows().to_csv(output_dir / "cities.csv", index=False)
    build_vehicle_rows().to_csv(output_dir / "vehicles.csv", index=False)
    build_driver_rows().to_csv(output_dir / "drivers.csv", index=False)
    shipments, trips, route_stops, delay_events = build_shipment_trip_route_rows()
    shipments.to_csv(output_dir / "shipments.csv", index=False)
    trips.to_csv(output_dir / "trips.csv", index=False)
    route_stops.to_csv(output_dir / "route_stops.csv", index=False)
    delay_events.to_csv(output_dir / "delay_events.csv", index=False)


def main() -> None:
    write_csvs(OUTPUT_DIR)
    print(f"Synthetic logistics CSVs written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
