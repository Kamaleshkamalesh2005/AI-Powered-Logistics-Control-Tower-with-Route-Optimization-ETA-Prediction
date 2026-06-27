import type {
  DashboardPayload,
  DelayCause,
  DelayCausePoint,
  DelayTrendPoint,
  KpiSummary,
  RoutePolyline,
  ShipmentRow,
  ShipmentStatus,
  VehiclePosition,
} from "../types/dashboard";

const hubLatLng: Record<string, [number, number]> = {
  Delhi: [28.6139, 77.209],
  Mumbai: [19.076, 72.8777],
  Bengaluru: [12.9716, 77.5946],
  Chennai: [13.0827, 80.2707],
  Kolkata: [22.5726, 88.3639],
  Hyderabad: [17.385, 78.4867],
  Pune: [18.5204, 73.8567],
  Ahmedabad: [23.0225, 72.5714],
  Jaipur: [26.9124, 75.7873],
  Surat: [21.1702, 72.8311],
};

const cityPairs: Array<[string, string]> = [
  ["Delhi", "Mumbai"],
  ["Mumbai", "Bengaluru"],
  ["Bengaluru", "Chennai"],
  ["Kolkata", "Hyderabad"],
  ["Pune", "Ahmedabad"],
  ["Jaipur", "Surat"],
];

const vehicleTypes = ["Tata Ace EV", "Ashok Leyland Bada Dost", "Mahindra Bolero Pik-Up", "Eicher Pro 2059", "Volvo FMX"];

const shipmentsStatusPalette: Record<ShipmentStatus, string> = {
  in_transit: "bg-sky-500/15 text-sky-300 ring-sky-400/30",
  delivered: "bg-emerald-500/15 text-emerald-300 ring-emerald-400/30",
  pending: "bg-amber-500/15 text-amber-300 ring-amber-400/30",
  exception: "bg-rose-500/15 text-rose-300 ring-rose-400/30",
};

function pseudoRandom(seed: number): number {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

function lerp(start: number, end: number, factor: number): number {
  return start + (end - start) * factor;
}

function interpolateRoute(start: [number, number], end: [number, number], steps: number, wave: number): [number, number][] {
  const coordinates: [number, number][] = [];
  for (let index = 0; index <= steps; index += 1) {
    const fraction = index / steps;
    const lat = lerp(start[0], end[0], fraction) + Math.sin(fraction * Math.PI) * wave;
    const lng = lerp(start[1], end[1], fraction) + Math.cos(fraction * Math.PI * 2) * wave * 0.9;
    coordinates.push([Number(lat.toFixed(4)), Number(lng.toFixed(4))]);
  }
  return coordinates;
}

function buildVehicles(): VehiclePosition[] {
  return Array.from({ length: 6 }, (_, index) => {
    const city = cityPairs[index][0];
    const [lat, lng] = hubLatLng[city];
    const offset = (index + 1) * 0.07;
    return {
      id: `veh-${index + 1}`,
      label: `Truck ${index + 1}`,
      type: vehicleTypes[index % vehicleTypes.length],
      latitude: Number((lat + offset).toFixed(4)),
      longitude: Number((lng + offset * 0.8).toFixed(4)),
      status: index % 4 === 0 ? "delayed" : index % 3 === 0 ? "idle" : "active",
      heading: 45 + index * 38,
      speedKmh: 38 + index * 7,
    };
  });
}

function buildRoutes(vehicles: VehiclePosition[]): RoutePolyline[] {
  return vehicles.map((vehicle, index) => {
    const [originName, destinationName] = cityPairs[index % cityPairs.length];
    const origin = hubLatLng[originName];
    const destination = hubLatLng[destinationName];
    return {
      id: `route-${vehicle.id}`,
      vehicleId: vehicle.id,
      coordinates: interpolateRoute(origin, destination, 7, 0.18 - index * 0.015),
      color: ["#22c55e", "#38bdf8", "#f97316", "#a855f7", "#f43f5e", "#14b8a6"][index % 6],
      distanceKm: Number((pseudoRandom(index + 1) * 1500 + 350).toFixed(1)),
    };
  });
}

function buildShipments(vehicles: VehiclePosition[]): ShipmentRow[] {
  const statuses: ShipmentStatus[] = ["in_transit", "delivered", "pending", "exception"];
  return Array.from({ length: 12 }, (_, index) => {
    const pair = cityPairs[index % cityPairs.length];
    const vehicle = vehicles[index % vehicles.length];
    const status = statuses[index % statuses.length];
    const delayMinutes = status === "delivered" ? Math.round(4 + pseudoRandom(index) * 16) : Math.round(10 + pseudoRandom(index + 3) * 80);
    return {
      id: `shp-${index + 1}`,
      reference: `SHP-${(200100 + index).toString()}`,
      customerName: `Customer ${index + 1}`,
      origin: pair[0],
      destination: pair[1],
      vehicleId: vehicle.id,
      status,
      etaMinutes: Math.round(80 + pseudoRandom(index + 9) * 240),
      delayMinutes,
      updatedAt: new Date(Date.now() - index * 1000 * 60 * 22).toISOString(),
    };
  });
}

function buildTrend(): DelayTrendPoint[] {
  const points: DelayTrendPoint[] = [];
  let movingAverage = 32;
  for (let index = 0; index < 12; index += 1) {
    const base = 20 + pseudoRandom(index + 2) * 35 + (index % 4 === 0 ? 12 : 0);
    movingAverage = index === 0 ? base : (movingAverage * 0.7 + base * 0.3);
    points.push({
      period: `W${index + 1}`,
      delayMinutes: Number(base.toFixed(1)),
      movingAverage: Number(movingAverage.toFixed(1)),
    });
  }
  return points;
}

function buildCauseBreakdown(): DelayCausePoint[] {
  const causes: DelayCause[] = ["traffic", "weather", "loading", "mechanical", "documentation"];
  return causes.map((cause, index) => ({
    cause,
    count: Math.round(12 + pseudoRandom(index + 11) * 28),
  }));
}

function buildKpis(shipments: ShipmentRow[]): KpiSummary {
  const activeShipments = shipments.filter((shipment) => shipment.status === "in_transit" || shipment.status === "pending").length;
  const onTimeCount = shipments.filter((shipment) => shipment.delayMinutes <= 15).length;
  const averageDelay = shipments.reduce((sum, shipment) => sum + shipment.delayMinutes, 0) / shipments.length;
  const exceptionQueue = shipments.filter((shipment) => shipment.status === "exception").length;
  return {
    onTimePercentage: Number(((onTimeCount / shipments.length) * 100).toFixed(1)),
    averageDelayMinutes: Number(averageDelay.toFixed(1)),
    activeShipments,
    exceptionQueue,
  };
}

async function wait(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

export async function fetchDashboardData(): Promise<DashboardPayload> {
  await wait(700);
  const vehicles = buildVehicles();
  const routes = buildRoutes(vehicles);
  const shipments = buildShipments(vehicles);
  const delayTrend = buildTrend();
  const delayByCause = buildCauseBreakdown();
  const kpis = buildKpis(shipments);
  return {
    kpis,
    vehicles,
    routes,
    shipments,
    delayTrend,
    delayByCause,
  };
}
