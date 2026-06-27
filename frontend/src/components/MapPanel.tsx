import { Icon, divIcon } from "leaflet";
import "leaflet/dist/leaflet.css";
import { MapContainer, Marker, Polyline, Popup, TileLayer } from "react-leaflet";

import type { RoutePolyline, VehiclePosition } from "../types/dashboard";

function statusColor(status: VehiclePosition["status"]) {
  if (status === "active") return "#22c55e";
  if (status === "idle") return "#38bdf8";
  if (status === "delayed") return "#f59e0b";
  return "#f43f5e";
}

function vehicleIcon(status: VehiclePosition["status"]) {
  return divIcon({
    className: "",
    html: `
      <div style="
        width: 18px;
        height: 18px;
        border-radius: 9999px;
        background: ${statusColor(status)};
        border: 3px solid rgba(4, 17, 29, 0.96);
        box-shadow: 0 0 0 8px rgba(255,255,255,0.08), 0 0 28px ${statusColor(status)}80;
      "></div>
    `,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
}

const mapIcon = new Icon.Default();
// Fix the default icon path for Vite bundling.
// @ts-expect-error Leaflet internal option patch.
mapIcon._getIconUrl = undefined;

export function MapPanel({ vehicles, routes }: { vehicles: VehiclePosition[]; routes: RoutePolyline[] }) {
  const center: [number, number] = [20.5937, 78.9629];

  return (
    <div className="overflow-hidden rounded-[2rem] border border-white/10 bg-white/5 shadow-glow backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-white/10 px-6 py-5">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Live map</p>
          <h2 className="mt-1 text-xl font-semibold text-white">Vehicle positions and optimized routes</h2>
        </div>
        <div className="rounded-full border border-slate-500/20 bg-slate-900/60 px-3 py-1 text-xs text-slate-300">
          India-wide network
        </div>
      </div>

      <MapContainer center={center} zoom={5} scrollWheelZoom={false} className="h-[520px] w-full">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {routes.map((route) => (
          <Polyline key={route.id} positions={route.coordinates} pathOptions={{ color: route.color, weight: 4, opacity: 0.85 }} />
        ))}
        {vehicles.map((vehicle) => (
          <Marker key={vehicle.id} position={[vehicle.latitude, vehicle.longitude]} icon={vehicleIcon(vehicle.status)}>
            <Popup>
              <div className="space-y-1">
                <p className="font-semibold">{vehicle.label}</p>
                <p className="text-xs">{vehicle.type}</p>
                <p className="text-xs">{vehicle.speedKmh} km/h</p>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
