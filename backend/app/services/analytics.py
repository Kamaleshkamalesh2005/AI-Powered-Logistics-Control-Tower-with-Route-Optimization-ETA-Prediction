from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum
from statistics import quantiles
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import String, and_, cast, func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.delay_event import DelayEvent
from app.models.shipment import Shipment
from app.models.trip import Trip
from app.models.vehicle import Vehicle
from app.schemas.analytics import (
    AnalyticsPeriod,
    CauseBreakdown,
    DelayAnalyticsRequest,
    DelayAnalyticsResponse,
    RouteDelayBreakdown,
    TimeSeriesPoint,
    VehicleDelayBreakdown,
)

REDIS_CLIENT: Redis | None = None


def _serialize_json(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Enum):  # type: ignore[name-defined]
        return value.value
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_redis(self) -> Redis | None:
        global REDIS_CLIENT
        if REDIS_CLIENT is None:
            try:
                REDIS_CLIENT = Redis.from_url(settings.redis_url, decode_responses=True)
                await REDIS_CLIENT.ping()
            except Exception:
                REDIS_CLIENT = None
        return REDIS_CLIENT

    def cache_key(self, payload: DelayAnalyticsRequest) -> str:
        raw = payload.model_dump(mode="json", exclude_none=True)
        digest = hashlib.sha256(json.dumps(raw, sort_keys=True).encode("utf-8")).hexdigest()
        return f"analytics:delays:{digest}"

    async def get_delay_analytics(self, payload: DelayAnalyticsRequest) -> DelayAnalyticsResponse:
        cache_key = self.cache_key(payload)
        redis_client = await self.get_redis()
        if redis_client is not None:
            cached = await redis_client.get(cache_key)
            if cached:
                cached_payload = json.loads(cached)
                cached_payload["cache_hit"] = True
                return DelayAnalyticsResponse.model_validate(cached_payload)

        response = await self._build_response(payload, cache_key, cache_hit=False)
        if redis_client is not None:
            await redis_client.setex(
                cache_key,
                settings.analytics_cache_ttl_seconds,
                json.dumps(response.model_dump(mode="json"), default=_serialize_json),
            )
        return response

    async def _build_response(
        self,
        payload: DelayAnalyticsRequest,
        cache_key: str,
        cache_hit: bool,
    ) -> DelayAnalyticsResponse:
        filters = [DelayEvent.occurred_at.is_not(None)]
        if payload.start_date is not None:
            filters.append(DelayEvent.occurred_at >= self._to_utc_datetime(payload.start_date))
        if payload.end_date is not None:
            filters.append(DelayEvent.occurred_at < self._to_utc_datetime(payload.end_date + timedelta(days=1)))
        if payload.min_delay_minutes is not None:
            filters.append(DelayEvent.delay_minutes >= payload.min_delay_minutes)
        if payload.route_names:
            filters.append(func.coalesce(Trip.route_name, Shipment.origin + literal(" -> ") + Shipment.destination).in_(payload.route_names))
        if payload.vehicle_ids:
            filters.append(Trip.vehicle_id.in_(payload.vehicle_ids))

        route_name_expr = func.coalesce(Trip.route_name, Shipment.origin + literal(" -> ") + Shipment.destination)
        vehicle_label_expr = func.coalesce(Vehicle.fleet_number, func.concat(literal("Vehicle-"), cast(Trip.vehicle_id, String)))
        period_expr = self._period_expression(payload.period)

        base_query = (
            select(
                DelayEvent.id,
                DelayEvent.delay_minutes,
                DelayEvent.reason_code,
                DelayEvent.occurred_at,
                route_name_expr.label("route_name"),
                Trip.vehicle_id.label("vehicle_id"),
                vehicle_label_expr.label("vehicle_label"),
                period_expr.label("period_start"),
            )
            .select_from(DelayEvent)
            .join(Trip, DelayEvent.trip_id == Trip.id)
            .outerjoin(Shipment, DelayEvent.shipment_id == Shipment.id)
            .outerjoin(Vehicle, Trip.vehicle_id == Vehicle.id)
            .where(and_(*filters))
        )

        rows = (await self.session.execute(base_query)).mappings().all()
        if not rows:
            return DelayAnalyticsResponse(
                period=payload.period,
                total_events=0,
                delayed_events=0,
                overall_delay_frequency=0.0,
                overall_avg_delay_minutes=0.0,
                anomaly_threshold_minutes=None,
                route_breakdown=[],
                vehicle_breakdown=[],
                time_series=[],
                cause_breakdown=[],
                cache_hit=cache_hit,
                cache_key=cache_key,
            )

        delay_values = [float(row["delay_minutes"]) for row in rows]
        anomaly_threshold = self._iqr_threshold(delay_values)

        route_breakdown = self._aggregate_route(rows, anomaly_threshold)
        vehicle_breakdown = self._aggregate_vehicle(rows, anomaly_threshold)
        time_series = self._aggregate_time_series(rows, anomaly_threshold)
        cause_breakdown = self._aggregate_causes(rows)

        total_events = len(rows)
        delayed_events = sum(1 for value in delay_values if value > 0)
        overall_avg_delay = round(sum(delay_values) / total_events, 2)
        overall_delay_frequency = round(delayed_events / total_events, 4)

        return DelayAnalyticsResponse(
            period=payload.period,
            total_events=total_events,
            delayed_events=delayed_events,
            overall_delay_frequency=overall_delay_frequency,
            overall_avg_delay_minutes=overall_avg_delay,
            anomaly_threshold_minutes=round(anomaly_threshold, 2) if anomaly_threshold is not None else None,
            route_breakdown=route_breakdown,
            vehicle_breakdown=vehicle_breakdown,
            time_series=time_series,
            cause_breakdown=cause_breakdown,
            cache_hit=cache_hit,
            cache_key=cache_key,
        )

    def _aggregate_route(self, rows: Iterable[dict[str, Any]], anomaly_threshold: float | None) -> list[RouteDelayBreakdown]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            grouped.setdefault(str(row["route_name"]), []).append(row)

        breakdown: list[RouteDelayBreakdown] = []
        for route_name, group_rows in sorted(grouped.items(), key=lambda item: item[0]):
            total_events = len(group_rows)
            delay_minutes = [float(row["delay_minutes"]) for row in group_rows]
            delayed_events = sum(1 for value in delay_minutes if value > 0)
            average_delay = sum(delay_minutes) / total_events
            breakdown.append(
                RouteDelayBreakdown(
                    route_name=route_name,
                    delay_frequency=round(delayed_events / total_events, 4),
                    avg_delay_minutes=round(average_delay, 2),
                    total_events=total_events,
                    delayed_events=delayed_events,
                    anomaly_flag=self._is_anomalous(average_delay, anomaly_threshold),
                )
            )
        return breakdown

    def _aggregate_vehicle(self, rows: Iterable[dict[str, Any]], anomaly_threshold: float | None) -> list[VehicleDelayBreakdown]:
        grouped: dict[int, list[dict[str, Any]]] = {}
        for row in rows:
            vehicle_id = int(row["vehicle_id"] or 0)
            grouped.setdefault(vehicle_id, []).append(row)

        breakdown: list[VehicleDelayBreakdown] = []
        for vehicle_id, group_rows in sorted(grouped.items(), key=lambda item: item[0]):
            total_events = len(group_rows)
            delay_minutes = [float(row["delay_minutes"]) for row in group_rows]
            delayed_events = sum(1 for value in delay_minutes if value > 0)
            average_delay = sum(delay_minutes) / total_events
            vehicle_label = str(group_rows[0]["vehicle_label"] or f"Vehicle-{vehicle_id}")
            breakdown.append(
                VehicleDelayBreakdown(
                    vehicle_id=vehicle_id,
                    vehicle_label=vehicle_label,
                    delay_frequency=round(delayed_events / total_events, 4),
                    avg_delay_minutes=round(average_delay, 2),
                    total_events=total_events,
                    delayed_events=delayed_events,
                    anomaly_flag=self._is_anomalous(average_delay, anomaly_threshold),
                )
            )
        return breakdown

    def _aggregate_time_series(self, rows: Iterable[dict[str, Any]], anomaly_threshold: float | None) -> list[TimeSeriesPoint]:
        grouped: dict[datetime, list[dict[str, Any]]] = {}
        for row in rows:
            grouped.setdefault(row["period_start"], []).append(row)

        series: list[TimeSeriesPoint] = []
        for period_start, group_rows in sorted(grouped.items(), key=lambda item: item[0]):
            total_events = len(group_rows)
            delay_minutes = [float(row["delay_minutes"]) for row in group_rows]
            delayed_events = sum(1 for value in delay_minutes if value > 0)
            average_delay = sum(delay_minutes) / total_events
            series.append(
                TimeSeriesPoint(
                    period_start=period_start,
                    total_events=total_events,
                    delayed_events=delayed_events,
                    delay_frequency=round(delayed_events / total_events, 4),
                    avg_delay_minutes=round(average_delay, 2),
                    anomaly_flag=self._is_anomalous(average_delay, anomaly_threshold),
                )
            )
        return series

    def _aggregate_causes(self, rows: Iterable[dict[str, Any]]) -> list[CauseBreakdown]:
        counts: dict[str, int] = {}
        for row in rows:
            cause = str(row["reason_code"] or "unspecified")
            counts[cause] = counts.get(cause, 0) + 1

        total = sum(counts.values()) or 1
        return [
            CauseBreakdown(cause=cause, count=count, share=round(count / total, 4))
            for cause, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)
        ]

    def _period_expression(self, period: AnalyticsPeriod):
        if period == AnalyticsPeriod.WEEK:
            return func.date_trunc("week", DelayEvent.occurred_at)
        if period == AnalyticsPeriod.MONTH:
            return func.date_trunc("month", DelayEvent.occurred_at)
        return func.date_trunc("day", DelayEvent.occurred_at)

    def _iqr_threshold(self, values: list[float]) -> float | None:
        if len(values) < 4:
            return None
        q1, q3 = quantiles(values, n=4, method="inclusive")[0], quantiles(values, n=4, method="inclusive")[2]
        return q3 + 1.5 * (q3 - q1)

    def _is_anomalous(self, value: float, threshold: float | None) -> bool:
        if threshold is None:
            return False
        return value > threshold

    def _to_utc_datetime(self, value: date) -> datetime:
        return datetime.combine(value, time.min, tzinfo=timezone.utc)
