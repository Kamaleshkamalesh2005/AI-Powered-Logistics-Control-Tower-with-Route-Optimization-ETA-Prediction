from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RouteStopInput(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    demand: int = Field(ge=0)
    label: str | None = Field(default=None, max_length=120)


class OptimizeRouteRequest(BaseModel):
    stops: list[RouteStopInput] = Field(min_length=1)
    vehicle_count: int = Field(ge=1, le=100)
    vehicle_capacity: int = Field(gt=0)
    depot_latitude: float | None = Field(default=None, ge=-90, le=90)
    depot_longitude: float | None = Field(default=None, ge=-180, le=180)
    average_speed_kmh: float = Field(default=40.0, gt=0)


class RouteStopResult(BaseModel):
    stop_index: int
    label: str | None = None
    latitude: float
    longitude: float
    demand: int
    distance_from_previous_km: float
    travel_time_minutes: float
    cumulative_distance_km: float
    cumulative_time_minutes: float


class VehicleRouteResult(BaseModel):
    vehicle_index: int
    stop_indices: list[int]
    total_demand: int
    total_distance_km: float
    estimated_time_minutes: float
    stops: list[RouteStopResult]


class OptimizeRouteResponse(BaseModel):
    algorithm: str
    used_fallback: bool
    depot_latitude: float
    depot_longitude: float
    total_distance_km: float
    estimated_time_minutes: float
    routes: list[VehicleRouteResult]
    unassigned_stop_indices: list[int]
    notes: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
