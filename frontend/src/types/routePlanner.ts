export interface RoutePlanStop {
  id: string;
  label: string;
  latitude: number;
  longitude: number;
  demand: number;
  address?: string;
  source?: "map" | "search";
}

export interface GeocodeSuggestion {
  displayName: string;
  latitude: number;
  longitude: number;
  type?: string;
}

export interface OptimizedRouteStop {
  stop_index: number;
  label: string | null;
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

export interface OptimizedRouteResponse {
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

export interface RoutePlanComparison {
  distanceKm: number;
  timeMinutes: number;
  costInr: number;
}
