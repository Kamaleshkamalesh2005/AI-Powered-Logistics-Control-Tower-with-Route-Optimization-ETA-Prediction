import { useEffect, useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { RoutePlannerMap } from "./RoutePlannerMap";
import type {
  GeocodeResult,
  OptimizeRouteRequest,
  OptimizeRouteResponse,
  OptimizedMapRoute,
  PlannedStop,
  RouteMetrics,
} from "../types/routePlanning";

const DEFAULT_DEPOT: [number, number] = [20.5937, 78.9629];
const AVERAGE_SPEED_KMH = 40;
const FUEL_COST_PER_KM = 9.75;
const ROUTE_COLORS = ["#22c55e", "#38bdf8", "#f97316", "#a855f7", "#f43f5e", "#14b8a6"];

const FALLBACK_LOCATIONS: Array<{ name: string; latitude: number; longitude: number; aliases: string[] }> = [
  { name: "Delhi", latitude: 28.6139, longitude: 77.209, aliases: ["new delhi", "delhi ncr"] },
  { name: "Mumbai", latitude: 19.076, longitude: 72.8777, aliases: ["bombay"] },
  { name: "Bengaluru", latitude: 12.9716, longitude: 77.5946, aliases: ["bangalore"] },
  { name: "Chennai", latitude: 13.0827, longitude: 80.2707, aliases: [] },
  { name: "Kolkata", latitude: 22.5726, longitude: 88.3639, aliases: ["calcutta"] },
  { name: "Hyderabad", latitude: 17.385, longitude: 78.4867, aliases: [] },
  { name: "Pune", latitude: 18.5204, longitude: 73.8567, aliases: [] },
  { name: "Ahmedabad", latitude: 23.0225, longitude: 72.5714, aliases: [] },
  { name: "Jaipur", latitude: 26.9124, longitude: 75.7873, aliases: [] },
  { name: "Surat", latitude: 21.1702, longitude: 72.8311, aliases: [] },
];

function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number) {
  const earthRadiusKm = 6371;
  const deltaLat = ((lat2 - lat1) * Math.PI) / 180;
  const deltaLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(deltaLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(deltaLon / 2) ** 2;
  return 2 * earthRadiusKm * Math.asin(Math.sqrt(a));
}

function makeId(prefix: string) {
  return `${prefix}-${globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`}`;
}

function buildRouteMetrics(points: [number, number][], speedKmh = AVERAGE_SPEED_KMH): RouteMetrics {
  if (points.length < 2) {
    return { distanceKm: 0, timeMinutes: 0, costInr: 0 };
  }

  let distanceKm = 0;
  for (let index = 0; index < points.length - 1; index += 1) {
    distanceKm += haversineKm(points[index][0], points[index][1], points[index + 1][0], points[index + 1][1]);
  }

  const timeMinutes = (distanceKm / speedKmh) * 60;
  const costInr = distanceKm * FUEL_COST_PER_KM;
  return {
    distanceKm: Number(distanceKm.toFixed(2)),
    timeMinutes: Number(timeMinutes.toFixed(1)),
    costInr: Number(costInr.toFixed(0)),
  };
}

function formatDistance(value: number) {
  return `${value.toFixed(1)} km`;
}

function formatMinutes(value: number) {
  return `${value.toFixed(1)} min`;
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0, style: "currency", currency: "INR" }).format(value);
}

function getFallbackGeocodeResults(query: string): GeocodeResult[] {
  const normalized = query.trim().toLowerCase();
  return FALLBACK_LOCATIONS.filter((location) => {
    return (
      location.name.toLowerCase().includes(normalized) ||
      location.aliases.some((alias) => alias.includes(normalized))
    );
  })
    .slice(0, 5)
    .map((location) => ({
      displayName: `${location.name}, India`,
      latitude: location.latitude,
      longitude: location.longitude,
    }));
}

async function geocodeAddress(query: string): Promise<GeocodeResult[]> {
  const response = await fetch(
    `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=5&countrycodes=in&q=${encodeURIComponent(query)}`,
    {
      headers: {
        Accept: "application/json",
      },
    },
  );

  if (!response.ok) {
    throw new Error("OpenStreetMap geocoding request failed");
  }

  const data = (await response.json()) as Array<{ display_name: string; lat: string; lon: string }>;
  return data.map((item) => ({
    displayName: item.display_name,
    latitude: Number.parseFloat(item.lat),
    longitude: Number.parseFloat(item.lon),
  }));
}

function createStop(latitude: number, longitude: number, name: string, source: PlannedStop["source"]): PlannedStop {
  return {
    id: makeId("stop"),
    name,
    latitude,
    longitude,
    demand: 1,
    source,
  };
}

function stopLabel(stop: PlannedStop, index: number) {
  return stop.name.trim().length > 0 ? stop.name : `Stop ${index + 1}`;
}

export function PlanRoutePage() {
  const [darkMode, setDarkMode] = useState(true);
  const [stops, setStops] = useState<PlannedStop[]>([]);
  const [vehicleCount, setVehicleCount] = useState(3);
  const [vehicleCapacity, setVehicleCapacity] = useState(120);
  const [addressQuery, setAddressQuery] = useState("");
  const [searchResults, setSearchResults] = useState<GeocodeResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [optimizedRoute, setOptimizedRoute] = useState<OptimizeRouteResponse | null>(null);
  const [geocodeMessage, setGeocodeMessage] = useState<string | null>(null);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

  useEffect(() => {
    setOptimizedRoute(null);
  }, [stops, vehicleCount, vehicleCapacity]);

  const depot = optimizedRoute ? ([optimizedRoute.depot_latitude, optimizedRoute.depot_longitude] as [number, number]) : DEFAULT_DEPOT;

  const naiveRoute = useMemo(() => {
    const routePoints: [number, number][] = [depot, ...stops.map((stop) => [stop.latitude, stop.longitude] as [number, number]), depot];
    return {
      path: routePoints,
      metrics: buildRouteMetrics(routePoints),
    };
  }, [depot, stops]);

  const optimizedMetrics = optimizedRoute
    ? {
        distanceKm: optimizedRoute.total_distance_km,
        timeMinutes: optimizedRoute.estimated_time_minutes,
        costInr: optimizedRoute.total_distance_km * FUEL_COST_PER_KM,
      }
    : null;

  const optimizedMapRoutes: OptimizedMapRoute[] = useMemo(() => {
    if (!optimizedRoute) {
      return [];
    }

    return optimizedRoute.routes.map((route, index) => {
      const routePoints: [number, number][] = [
        depot,
        ...route.stops.map((stop) => [stop.latitude, stop.longitude] as [number, number]),
        depot,
      ];
      return {
        id: `optimized-${route.vehicle_index}`,
        label: `Vehicle ${route.vehicle_index}`,
        color: ROUTE_COLORS[index % ROUTE_COLORS.length],
        coordinates: routePoints,
        distanceKm: route.total_distance_km,
        timeMinutes: route.estimated_time_minutes,
      };
    });
  }, [depot, optimizedRoute]);

  const routeComparison = optimizedMetrics
    ? {
        distanceSavingsKm: Number((naiveRoute.metrics.distanceKm - optimizedMetrics.distanceKm).toFixed(2)),
        timeSavingsMinutes: Number((naiveRoute.metrics.timeMinutes - optimizedMetrics.timeMinutes).toFixed(1)),
        costSavingsInr: Number((naiveRoute.metrics.costInr - optimizedMetrics.costInr).toFixed(0)),
      }
    : null;

  const optimizeMutation = useMutation({
    mutationFn: async () => {
      if (stops.length === 0) {
        throw new Error("Add at least one stop before optimizing.");
      }

      const payload: OptimizeRouteRequest = {
        stops: stops.map((stop) => ({
          latitude: stop.latitude,
          longitude: stop.longitude,
          demand: stop.demand,
          label: stop.name,
        })),
        vehicle_count: vehicleCount,
        vehicle_capacity: vehicleCapacity,
        depot_latitude: depot[0],
        depot_longitude: depot[1],
        average_speed_kmh: AVERAGE_SPEED_KMH,
      };

      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api"}/optimize-route`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || "Failed to optimize route");
      }

      return (await response.json()) as OptimizeRouteResponse;
    },
    onSuccess: (data) => {
      setOptimizedRoute(data);
    },
  });

  async function handleGeocodeSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const query = addressQuery.trim();
    if (!query) {
      setSearchResults([]);
      setSearchError("Enter an address or city to search.");
      return;
    }

    setSearchLoading(true);
    setSearchError(null);
    setGeocodeMessage(null);

    try {
      const results = await geocodeAddress(query);
      if (results.length === 0) {
        const fallback = getFallbackGeocodeResults(query);
        setSearchResults(fallback);
        setGeocodeMessage(fallback.length > 0 ? "Using offline fallback locations." : "No geocoding results found.");
      } else {
        setSearchResults(results);
      }
    } catch {
      const fallback = getFallbackGeocodeResults(query);
      setSearchResults(fallback);
      setGeocodeMessage(fallback.length > 0 ? "OpenStreetMap unavailable, using offline fallback locations." : "No geocoding results found.");
      if (fallback.length === 0) {
        setSearchError("OpenStreetMap geocoding failed and no offline matches were found.");
      }
    } finally {
      setSearchLoading(false);
    }
  }

  function addStopFromMap(latitude: number, longitude: number) {
    setStops((currentStops) => [
      ...currentStops,
      createStop(latitude, longitude, `Stop ${currentStops.length + 1}`, "map"),
    ]);
    setSearchResults([]);
    setSearchError(null);
    setGeocodeMessage(null);
  }

  function addStopFromGeocode(result: GeocodeResult) {
    setStops((currentStops) => [
      ...currentStops,
      createStop(result.latitude, result.longitude, result.displayName, "search"),
    ]);
    setSearchResults([]);
    setAddressQuery("");
    setGeocodeMessage(null);
  }

  function updateStop(stopId: string, patch: Partial<PlannedStop>) {
    setStops((currentStops) => currentStops.map((stop) => (stop.id === stopId ? { ...stop, ...patch } : stop)));
  }

  function removeStop(stopId: string) {
    setStops((currentStops) => currentStops.filter((stop) => stop.id !== stopId));
  }

  function clearStops() {
    setStops([]);
    setOptimizedRoute(null);
    setSearchResults([]);
  }

  const isLoadingOptimization = optimizeMutation.isPending;

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(45,212,191,0.18),_transparent_28%),radial-gradient(circle_at_top_right,_rgba(251,191,36,0.12),_transparent_24%),linear-gradient(180deg,_#04111d_0%,_#071425_52%,_#06101a_100%)] text-slate-100 transition-colors duration-300 dark:bg-[radial-gradient(circle_at_top_left,_rgba(56,189,248,0.22),_transparent_26%),radial-gradient(circle_at_bottom_right,_rgba(168,85,247,0.14),_transparent_24%),linear-gradient(180deg,_#020617_0%,_#0f172a_52%,_#020617_100%)]">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-6 flex flex-col gap-4 rounded-[2rem] border border-white/10 bg-white/5 px-5 py-4 shadow-glow backdrop-blur-xl md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.38em] text-slate-400">Control Tower</p>
            <h1 className="mt-2 text-2xl font-semibold text-white sm:text-3xl">Plan Route</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-300">
              Add delivery stops on the map or by address search, then optimize a capacity-constrained route plan and compare it against a naive sequential route.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="rounded-full border border-white/10 bg-slate-950/50 px-4 py-2 text-xs text-slate-300">
              Nominatim geocoding + OR-Tools optimization
            </div>
            <button
              type="button"
              onClick={() => setDarkMode((current) => !current)}
              className="rounded-full border border-sky-400/20 bg-sky-500/10 px-4 py-2 text-sm font-semibold text-sky-100 transition hover:bg-sky-500/20"
            >
              {darkMode ? "Switch to light" : "Switch to dark"}
            </button>
          </div>
        </header>

        <main className="grid gap-6 xl:grid-cols-[1.35fr_0.85fr]">
          <section className="space-y-6">
            <div className="rounded-[2rem] border border-white/10 bg-white/5 p-6 shadow-glow backdrop-blur-xl">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Stop search</p>
                  <h2 className="mt-1 text-xl font-semibold text-white">Search address via OpenStreetMap</h2>
                </div>
                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">
                  Click the map to drop a pin
                </span>
              </div>

              <form className="mt-5 flex flex-col gap-3 lg:flex-row" onSubmit={handleGeocodeSearch}>
                <input
                  value={addressQuery}
                  onChange={(event) => setAddressQuery(event.target.value)}
                  placeholder="Search an address, landmark, city, or warehouse"
                  className="flex-1 rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-sky-400/40"
                />
                <button
                  type="submit"
                  className="rounded-2xl bg-sky-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-sky-600 disabled:cursor-not-allowed disabled:bg-slate-600"
                  disabled={searchLoading}
                >
                  {searchLoading ? "Searching..." : "Search address"}
                </button>
              </form>

              {searchError ? (
                <div className="mt-4 rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                  {searchError}
                </div>
              ) : null}
              {geocodeMessage ? (
                <div className="mt-4 rounded-2xl border border-amber-400/20 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
                  {geocodeMessage}
                </div>
              ) : null}

              <div className="mt-5 space-y-3">
                {searchLoading ? (
                  Array.from({ length: 3 }).map((_, index) => (
                    <div key={index} className="animate-pulse rounded-2xl border border-white/10 bg-white/5 p-4">
                      <div className="h-4 w-40 rounded-full bg-white/10" />
                      <div className="mt-3 h-3 w-56 rounded-full bg-white/10" />
                    </div>
                  ))
                ) : searchResults.length > 0 ? (
                  searchResults.map((result) => (
                    <div key={`${result.displayName}-${result.latitude}`} className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-slate-950/50 p-4 lg:flex-row lg:items-center lg:justify-between">
                      <div>
                        <p className="font-semibold text-white">{result.displayName}</p>
                        <p className="mt-1 text-xs text-slate-400">
                          {result.latitude.toFixed(4)}, {result.longitude.toFixed(4)}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => addStopFromGeocode(result)}
                        className="rounded-full border border-sky-400/20 bg-sky-500/10 px-4 py-2 text-xs font-semibold text-sky-100 transition hover:bg-sky-500/20"
                      >
                        Add stop
                      </button>
                    </div>
                  ))
                ) : (
                  <div className="rounded-2xl border border-dashed border-white/10 bg-white/5 p-4 text-sm text-slate-400">
                    Search results appear here. Use Nominatim or the offline fallback list when the address service is unavailable.
                  </div>
                )}
              </div>
            </div>

            <RoutePlannerMap depot={depot} stops={stops} naiveRoute={naiveRoute.path} optimizedRoutes={optimizedMapRoutes} onMapClick={addStopFromMap} />

            <section className="rounded-[2rem] border border-white/10 bg-white/5 p-6 shadow-glow backdrop-blur-xl">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Route comparison</p>
                  <h2 className="mt-1 text-xl font-semibold text-white">Naive route vs optimized route</h2>
                </div>
                <button
                  type="button"
                  onClick={() => optimizeMutation.mutate()}
                  disabled={stops.length === 0 || isLoadingOptimization}
                  className="rounded-2xl bg-emerald-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-600 disabled:cursor-not-allowed disabled:bg-slate-600"
                >
                  {isLoadingOptimization ? "Optimizing..." : "Optimize"}
                </button>
              </div>

              {optimizeMutation.isError ? (
                <div className="mt-4 rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                  {(optimizeMutation.error as Error).message}
                </div>
              ) : null}

              <div className="mt-5 grid gap-4 md:grid-cols-2">
                <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-5">
                  <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Naive route</p>
                  <div className="mt-4 space-y-3 text-sm text-slate-200">
                    <MetricLine label="Distance" value={formatDistance(naiveRoute.metrics.distanceKm)} />
                    <MetricLine label="Time" value={formatMinutes(naiveRoute.metrics.timeMinutes)} />
                    <MetricLine label="Fuel cost" value={formatCurrency(naiveRoute.metrics.costInr)} />
                    <MetricLine label="Stops" value={`${stops.length}`} />
                  </div>
                </div>

                <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-5">
                  <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Optimized route</p>
                  {optimizedMetrics ? (
                    <div className="mt-4 space-y-3 text-sm text-slate-200">
                      <MetricLine label="Distance" value={formatDistance(optimizedMetrics.distanceKm)} />
                      <MetricLine label="Time" value={formatMinutes(optimizedMetrics.timeMinutes)} />
                      <MetricLine label="Fuel cost" value={formatCurrency(optimizedMetrics.costInr)} />
                      <MetricLine label="Algorithm" value={optimizedRoute?.algorithm ?? "unknown"} />
                    </div>
                  ) : (
                    <div className="mt-4 space-y-3 animate-pulse">
                      <div className="h-4 w-32 rounded-full bg-white/10" />
                      <div className="h-4 w-28 rounded-full bg-white/10" />
                      <div className="h-4 w-36 rounded-full bg-white/10" />
                    </div>
                  )}
                </div>
              </div>

              {routeComparison ? (
                <div className="mt-5 grid gap-3 sm:grid-cols-3">
                  <SavingsCard label="Distance saved" value={formatDistance(routeComparison.distanceSavingsKm)} tone="text-emerald-300" />
                  <SavingsCard label="Time saved" value={formatMinutes(routeComparison.timeSavingsMinutes)} tone="text-sky-300" />
                  <SavingsCard label="Cost saved" value={formatCurrency(routeComparison.costSavingsInr)} tone="text-amber-300" />
                </div>
              ) : null}
            </section>
          </section>

          <aside className="space-y-6">
            <section className="rounded-[2rem] border border-white/10 bg-white/5 p-6 shadow-glow backdrop-blur-xl">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Controls</p>
                  <h2 className="mt-1 text-xl font-semibold text-white">Vehicle count and capacity</h2>
                </div>
                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">
                  Depot: control tower hub
                </span>
              </div>

              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="mb-2 block text-xs uppercase tracking-[0.25em] text-slate-400">Vehicles</span>
                  <input
                    type="number"
                    min={1}
                    max={100}
                    value={vehicleCount}
                    onChange={(event) => setVehicleCount(Number(event.target.value))}
                    className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-sky-400/40"
                  />
                </label>
                <label className="block">
                  <span className="mb-2 block text-xs uppercase tracking-[0.25em] text-slate-400">Capacity</span>
                  <input
                    type="number"
                    min={1}
                    value={vehicleCapacity}
                    onChange={(event) => setVehicleCapacity(Number(event.target.value))}
                    className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-sky-400/40"
                  />
                </label>
              </div>

              <div className="mt-5 flex items-center gap-3 text-sm text-slate-300">
                <div className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
                Add stops from the map or search results, then optimize.
              </div>
            </section>

            <section className="rounded-[2rem] border border-white/10 bg-white/5 p-6 shadow-glow backdrop-blur-xl">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Stops</p>
                  <h2 className="mt-1 text-xl font-semibold text-white">Delivery list</h2>
                </div>
                <button
                  type="button"
                  onClick={clearStops}
                  disabled={stops.length === 0}
                  className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Clear all
                </button>
              </div>

              <div className="mt-5 space-y-3">
                {stops.length > 0 ? (
                  stops.map((stop, index) => (
                    <article key={stop.id} className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Stop {index + 1}</p>
                          <input
                            value={stop.name}
                            onChange={(event) => updateStop(stop.id, { name: event.target.value })}
                            className="mt-2 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none transition focus:border-sky-400/40"
                          />
                        </div>
                        <button
                          type="button"
                          onClick={() => removeStop(stop.id)}
                          className="rounded-full border border-rose-400/20 bg-rose-500/10 px-3 py-1 text-xs font-semibold text-rose-200 transition hover:bg-rose-500/20"
                        >
                          Remove
                        </button>
                      </div>

                      <div className="mt-4 grid grid-cols-2 gap-3 text-xs text-slate-400">
                        <div>
                          <p>Latitude</p>
                          <p className="mt-1 text-sm text-slate-200">{stop.latitude.toFixed(5)}</p>
                        </div>
                        <div>
                          <p>Longitude</p>
                          <p className="mt-1 text-sm text-slate-200">{stop.longitude.toFixed(5)}</p>
                        </div>
                        <label className="col-span-2 block">
                          <span className="mb-1 block">Demand</span>
                          <input
                            type="number"
                            min={0}
                            value={stop.demand}
                            onChange={(event) => updateStop(stop.id, { demand: Number(event.target.value) })}
                            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none transition focus:border-sky-400/40"
                          />
                        </label>
                      </div>
                    </article>
                  ))
                ) : (
                  <div className="rounded-2xl border border-dashed border-white/10 bg-white/5 p-6 text-sm text-slate-400">
                    No stops added yet. Click on the map or search an address to begin planning.
                  </div>
                )}
              </div>
            </section>

            <section className="rounded-[2rem] border border-white/10 bg-white/5 p-6 shadow-glow backdrop-blur-xl">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Routes</p>
                  <h2 className="mt-1 text-xl font-semibold text-white">Optimized assignments</h2>
                </div>
                {optimizedRoute ? (
                  <span className={`rounded-full px-3 py-1 text-xs font-semibold ${optimizedRoute.used_fallback ? "bg-amber-500/10 text-amber-200" : "bg-emerald-500/10 text-emerald-200"}`}>
                    {optimizedRoute.used_fallback ? "Fallback used" : "OR-Tools"}
                  </span>
                ) : (
                  <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">Waiting</span>
                )}
              </div>

              <div className="mt-5 space-y-3">
                {optimizedMapRoutes.length > 0 ? (
                  optimizedMapRoutes.map((route) => (
                    <article key={route.id} className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <span className="h-3 w-3 rounded-full" style={{ backgroundColor: route.color }} />
                          <p className="font-semibold text-white">{route.label}</p>
                        </div>
                        <p className="text-xs text-slate-400">{formatDistance(route.distanceKm)}</p>
                      </div>
                      <div className="mt-3 grid grid-cols-2 gap-3 text-sm text-slate-300">
                        <div>
                          <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Time</p>
                          <p className="mt-1 text-white">{formatMinutes(route.timeMinutes)}</p>
                        </div>
                        <div>
                          <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Route</p>
                          <p className="mt-1 text-white">{Math.max(route.coordinates.length - 2, 0)} stops</p>
                        </div>
                      </div>
                    </article>
                  ))
                ) : (
                  <div className="rounded-2xl border border-dashed border-white/10 bg-white/5 p-6 text-sm text-slate-400">
                    Optimized routes appear here after you click Optimize.
                  </div>
                )}
              </div>

              {optimizedRoute?.notes.length ? (
                <div className="mt-5 rounded-2xl border border-white/10 bg-slate-950/50 p-4">
                  <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Solver notes</p>
                  <ul className="mt-3 space-y-2 text-sm text-slate-300">
                    {optimizedRoute.notes.map((note) => (
                      <li key={note} className="flex gap-2">
                        <span className="mt-1 h-1.5 w-1.5 rounded-full bg-sky-400" />
                        <span>{note}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </section>
          </aside>
        </main>
      </div>
    </div>
  );
}

function MetricLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-2xl border border-white/8 bg-white/5 px-4 py-3">
      <span className="text-slate-400">{label}</span>
      <span className="font-semibold text-white">{value}</span>
    </div>
  );
}

function SavingsCard({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
      <p className="text-xs uppercase tracking-[0.24em] text-slate-500">{label}</p>
      <p className={`mt-2 text-lg font-semibold ${tone}`}>{value}</p>
    </div>
  );
}
