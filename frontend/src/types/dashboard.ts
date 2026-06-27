export type VehicleStatus = "active" | "idle" | "delayed" | "offline";
export type ShipmentStatus = "in_transit" | "delivered" | "pending" | "exception";
export type DelayCause = "traffic" | "weather" | "loading" | "mechanical" | "documentation";

export interface VehiclePosition {
  id: string;
  label: string;
  type: string;
  latitude: number;
  longitude: number;
  status: VehicleStatus;
  heading: number;
  speedKmh: number;
}

export interface RoutePolyline {
  id: string;
  vehicleId: string;
  coordinates: [number, number][];
  color: string;
  distanceKm: number;
}

export interface KpiSummary {
  onTimePercentage: number;
  averageDelayMinutes: number;
  activeShipments: number;
  exceptionQueue: number;
}

export interface ShipmentRow {
  id: string;
  reference: string;
  customerName: string;
  origin: string;
  destination: string;
  vehicleId: string;
  status: ShipmentStatus;
  etaMinutes: number;
  delayMinutes: number;
  updatedAt: string;
}

export interface DelayTrendPoint {
  period: string;
  delayMinutes: number;
  movingAverage: number;
}

export interface DelayCausePoint {
  cause: DelayCause;
  count: number;
}

export interface DashboardPayload {
  kpis: KpiSummary;
  vehicles: VehiclePosition[];
  routes: RoutePolyline[];
  shipments: ShipmentRow[];
  delayTrend: DelayTrendPoint[];
  delayByCause: DelayCausePoint[];
}
