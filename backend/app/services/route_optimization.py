from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from typing import Any

from fastapi import HTTPException, status

from app.schemas.route_optimization import (
    OptimizeRouteRequest,
    OptimizeRouteResponse,
    RouteStopInput,
    RouteStopResult,
    VehicleRouteResult,
)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    a = sin(delta_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(delta_lon / 2) ** 2
    return 2 * earth_radius_km * asin(sqrt(a))


def travel_time_minutes(distance_km: float, average_speed_kmh: float) -> float:
    return (distance_km / average_speed_kmh) * 60.0


@dataclass(slots=True)
class RouteNode:
    index: int
    latitude: float
    longitude: float
    demand: int
    label: str | None = None


class RouteOptimizationService:
    def optimize(self, payload: OptimizeRouteRequest) -> OptimizeRouteResponse:
        depot_latitude, depot_longitude, notes = self._resolve_depot(payload)
        nodes = self._build_nodes(payload.stops)
        distance_matrix = self._build_distance_matrix(depot_latitude, depot_longitude, nodes)

        try:
            return self._solve_with_ortools(payload, nodes, distance_matrix, depot_latitude, depot_longitude, notes)
        except Exception as exc:
            fallback_response = self._solve_with_nearest_neighbor(
                payload=payload,
                nodes=nodes,
                distance_matrix=distance_matrix,
                depot_latitude=depot_latitude,
                depot_longitude=depot_longitude,
                notes=notes,
            )
            fallback_response.notes.append(f"OR-Tools solver fallback activated: {exc.__class__.__name__}")
            return fallback_response

    def _resolve_depot(self, payload: OptimizeRouteRequest) -> tuple[float, float, list[str]]:
        notes: list[str] = []
        if payload.depot_latitude is not None and payload.depot_longitude is not None:
            return payload.depot_latitude, payload.depot_longitude, notes

        first_stop = payload.stops[0]
        notes.append("Depot not provided; using the first stop as the route origin.")
        return first_stop.latitude, first_stop.longitude, notes

    def _build_nodes(self, stops: list[RouteStopInput]) -> list[RouteNode]:
        return [
            RouteNode(index=stop_index + 1, latitude=stop.latitude, longitude=stop.longitude, demand=stop.demand, label=stop.label)
            for stop_index, stop in enumerate(stops)
        ]

    def _build_distance_matrix(
        self,
        depot_latitude: float,
        depot_longitude: float,
        nodes: list[RouteNode],
    ) -> list[list[float]]:
        points = [RouteNode(index=0, latitude=depot_latitude, longitude=depot_longitude, demand=0, label="Depot"), *nodes]
        matrix: list[list[float]] = []
        for origin in points:
            row: list[float] = []
            for destination in points:
                row.append(haversine_km(origin.latitude, origin.longitude, destination.latitude, destination.longitude))
            matrix.append(row)
        return matrix

    def _solve_with_ortools(
        self,
        payload: OptimizeRouteRequest,
        nodes: list[RouteNode],
        distance_matrix: list[list[float]],
        depot_latitude: float,
        depot_longitude: float,
        notes: list[str],
    ) -> OptimizeRouteResponse:
        try:
            from ortools.constraint_solver import pywrapcp, routing_enums_pb2
        except ImportError as exc:
            raise RuntimeError("ortools is not installed") from exc

        manager = pywrapcp.RoutingIndexManager(len(distance_matrix), payload.vehicle_count, 0)
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index: int, to_index: int) -> int:
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(distance_matrix[from_node][to_node] * 1000)

        def demand_callback(from_index: int) -> int:
            node = manager.IndexToNode(from_index)
            if node == 0:
                return 0
            return nodes[node - 1].demand

        distance_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(distance_callback_index)

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,
            [payload.vehicle_capacity] * payload.vehicle_count,
            True,
            "Capacity",
        )

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        search_parameters.time_limit.FromSeconds(5)

        solution = routing.SolveWithParameters(search_parameters)
        if solution is None:
            raise RuntimeError("OR-Tools did not produce a solution within the time limit")

        routes = self._extract_routes(
            manager=manager,
            routing=routing,
            solution=solution,
            nodes=nodes,
            distance_matrix=distance_matrix,
            payload=payload,
            depot_latitude=depot_latitude,
            depot_longitude=depot_longitude,
        )
        total_distance = round(sum(route.total_distance_km for route in routes), 3)
        total_time = round(sum(route.estimated_time_minutes for route in routes), 2)
        return OptimizeRouteResponse(
            algorithm="ortools",
            used_fallback=False,
            depot_latitude=depot_latitude,
            depot_longitude=depot_longitude,
            total_distance_km=total_distance,
            estimated_time_minutes=total_time,
            routes=routes,
            unassigned_stop_indices=self._detect_unassigned_stop_indices(routes, len(nodes)),
            notes=notes,
        )

    def _extract_routes(
        self,
        manager: Any,
        routing: Any,
        solution: Any,
        nodes: list[RouteNode],
        distance_matrix: list[list[float]],
        payload: OptimizeRouteRequest,
        depot_latitude: float,
        depot_longitude: float,
    ) -> list[VehicleRouteResult]:
        routes: list[VehicleRouteResult] = []
        for vehicle_index in range(payload.vehicle_count):
            index = routing.Start(vehicle_index)
            route_stop_results: list[RouteStopResult] = []
            stop_indices: list[int] = []
            cumulative_distance = 0.0
            cumulative_time = 0.0
            load = 0
            previous_node = 0

            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                if node != 0:
                    route_node = nodes[node - 1]
                    distance_from_previous = distance_matrix[previous_node][node]
                    travel_minutes = travel_time_minutes(distance_from_previous, payload.average_speed_kmh)
                    cumulative_distance += distance_from_previous
                    cumulative_time += travel_minutes
                    load += route_node.demand
                    stop_indices.append(route_node.index)
                    route_stop_results.append(
                        RouteStopResult(
                            stop_index=route_node.index,
                            label=route_node.label,
                            latitude=route_node.latitude,
                            longitude=route_node.longitude,
                            demand=route_node.demand,
                            distance_from_previous_km=round(distance_from_previous, 3),
                            travel_time_minutes=round(travel_minutes, 2),
                            cumulative_distance_km=round(cumulative_distance, 3),
                            cumulative_time_minutes=round(cumulative_time, 2),
                        )
                    )
                    previous_node = node

                index = solution.Value(routing.NextVar(index))

            return_distance = distance_matrix[previous_node][0]
            return_time = travel_time_minutes(return_distance, payload.average_speed_kmh)
            cumulative_distance += return_distance
            cumulative_time += return_time

            routes.append(
                VehicleRouteResult(
                    vehicle_index=vehicle_index + 1,
                    stop_indices=stop_indices,
                    total_demand=load,
                    total_distance_km=round(cumulative_distance, 3),
                    estimated_time_minutes=round(cumulative_time, 2),
                    stops=route_stop_results,
                )
            )
        return routes

    def _detect_unassigned_stop_indices(self, routes: list[VehicleRouteResult], total_stops: int) -> list[int]:
        assigned = {stop_index for route in routes for stop_index in route.stop_indices}
        return [stop_index for stop_index in range(1, total_stops + 1) if stop_index not in assigned]

    def _solve_with_nearest_neighbor(
        self,
        payload: OptimizeRouteRequest,
        nodes: list[RouteNode],
        distance_matrix: list[list[float]],
        depot_latitude: float,
        depot_longitude: float,
        notes: list[str],
    ) -> OptimizeRouteResponse:
        remaining = nodes[:]
        routes: list[VehicleRouteResult] = []

        for vehicle_number in range(1, payload.vehicle_count + 1):
            route_nodes: list[RouteNode] = []
            route_stop_results: list[RouteStopResult] = []
            cumulative_distance = 0.0
            cumulative_time = 0.0
            load = 0
            current_latitude = depot_latitude
            current_longitude = depot_longitude
            current_node_index = 0

            while remaining:
                candidates = [node for node in remaining if load + node.demand <= payload.vehicle_capacity]
                if not candidates:
                    break
                next_node = min(
                    candidates,
                    key=lambda node: haversine_km(current_latitude, current_longitude, node.latitude, node.longitude),
                )
                distance_from_previous = haversine_km(current_latitude, current_longitude, next_node.latitude, next_node.longitude)
                travel_minutes = travel_time_minutes(distance_from_previous, payload.average_speed_kmh)
                cumulative_distance += distance_from_previous
                cumulative_time += travel_minutes
                load += next_node.demand
                route_nodes.append(next_node)
                route_stop_results.append(
                    RouteStopResult(
                        stop_index=next_node.index,
                        label=next_node.label,
                        latitude=next_node.latitude,
                        longitude=next_node.longitude,
                        demand=next_node.demand,
                        distance_from_previous_km=round(distance_from_previous, 3),
                        travel_time_minutes=round(travel_minutes, 2),
                        cumulative_distance_km=round(cumulative_distance, 3),
                        cumulative_time_minutes=round(cumulative_time, 2),
                    )
                )
                current_latitude = next_node.latitude
                current_longitude = next_node.longitude
                current_node_index = next_node.index
                remaining.remove(next_node)

            if route_nodes:
                return_distance = haversine_km(current_latitude, current_longitude, depot_latitude, depot_longitude)
                cumulative_distance += return_distance
                cumulative_time += travel_time_minutes(return_distance, payload.average_speed_kmh)

            routes.append(
                VehicleRouteResult(
                    vehicle_index=vehicle_number,
                    stop_indices=[stop.index for stop in route_nodes],
                    total_demand=load,
                    total_distance_km=round(cumulative_distance, 3),
                    estimated_time_minutes=round(cumulative_time, 2),
                    stops=route_stop_results,
                )
            )

        total_distance = round(sum(route.total_distance_km for route in routes), 3)
        total_time = round(sum(route.estimated_time_minutes for route in routes), 2)
        unassigned_stop_indices = [node.index for node in remaining]
        if unassigned_stop_indices:
            notes.append("Some stops could not be assigned within capacity and vehicle constraints.")

        return OptimizeRouteResponse(
            algorithm="nearest_neighbor",
            used_fallback=True,
            depot_latitude=depot_latitude,
            depot_longitude=depot_longitude,
            total_distance_km=total_distance,
            estimated_time_minutes=total_time,
            routes=routes,
            unassigned_stop_indices=unassigned_stop_indices,
            notes=notes,
        )
