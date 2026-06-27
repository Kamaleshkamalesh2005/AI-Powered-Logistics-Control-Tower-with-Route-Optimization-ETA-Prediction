from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AnalyticsPeriod(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class DelayAnalyticsRequest(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    period: AnalyticsPeriod = AnalyticsPeriod.DAY
    route_names: list[str] | None = Field(default=None, max_length=100)
    vehicle_ids: list[int] | None = Field(default=None, max_length=100)
    min_delay_minutes: int | None = Field(default=None, ge=0)


class RouteDelayBreakdown(BaseModel):
    route_name: str
    delay_frequency: float
    avg_delay_minutes: float
    total_events: int
    delayed_events: int
    anomaly_flag: bool


class VehicleDelayBreakdown(BaseModel):
    vehicle_id: int
    vehicle_label: str
    delay_frequency: float
    avg_delay_minutes: float
    total_events: int
    delayed_events: int
    anomaly_flag: bool


class TimeSeriesPoint(BaseModel):
    period_start: datetime
    total_events: int
    delayed_events: int
    delay_frequency: float
    avg_delay_minutes: float
    anomaly_flag: bool


class CauseBreakdown(BaseModel):
    cause: str
    count: int
    share: float


class DelayAnalyticsResponse(BaseModel):
    period: AnalyticsPeriod
    total_events: int
    delayed_events: int
    overall_delay_frequency: float
    overall_avg_delay_minutes: float
    anomaly_threshold_minutes: float | None
    route_breakdown: list[RouteDelayBreakdown]
    vehicle_breakdown: list[VehicleDelayBreakdown]
    time_series: list[TimeSeriesPoint]
    cause_breakdown: list[CauseBreakdown]
    cache_hit: bool
    cache_key: str

    model_config = ConfigDict(from_attributes=True)
