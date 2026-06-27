export interface PlannedStop {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  demand: number;
  source: "map" | "search";
}

export interface GeocodeResult {
  displayName: string;
  latitude: number;
  longitude: number;
}

export interface OptimizeRouteRequest {
  stops: Array<{
    latitude: number;
    longitude: number;
    demand: number;
    label?: string;
  }>;
  vehicle_count: number;
  vehicle_capacity: number;
  depot_latitude?: number;
  depot_longitude?: number;
  average_speed_kmh?: number;
}

export interface OptimizedRouteStop {
  stop_index: number;
  label?: string | null;
  latitude: number;
  longitude: number;
  demand: number;
  distance_from_previous_km: number;
  travel_time_minutes: number;
  cumulative_distance_km: number;
  cumulative_time_minutes: number;
}

export interface OptimizedVehicleRoute {
  vehicle_index: number;
  stop_indices: number[];
  total_demand: number;
  total_distance_km: number;
  estimated_time_minutes: number;
  stops: OptimizedRouteStop[];
}

export interface OptimizeRouteResponse {
  algorithm: string;
  used_fallback: boolean;
  depot_latitude: number;
  depot_longitude: number;
  total_distance_km: number;
  estimated_time_minutes: number;
  routes: OptimizedVehicleRoute[];
  unassigned_stop_indices: number[];
  notes: string[];
}

export interface RouteMetrics {
  distanceKm: number;
  timeMinutes: number;
  costInr: number;
}

export interface OptimizedMapRoute {
  id: string;
  label: string;
  color: string;
  coordinates: [number, number][];
  distanceKm: number;
  timeMinutes: number;
}
