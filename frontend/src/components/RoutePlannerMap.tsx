import { divIcon } from "leaflet";
import "leaflet/dist/leaflet.css";
import { MapContainer, Marker, Polyline, Popup, TileLayer, useMapEvents } from "react-leaflet";

import type { OptimizedMapRoute, PlannedStop } from "../types/routePlanning";

const depotIcon = divIcon({
  className: "",
  html: `
    <div style="
      width: 22px;
      height: 22px;
      border-radius: 9999px;
      background: #14b8a6;
      border: 3px solid rgba(4, 17, 29, 0.96);
      box-shadow: 0 0 0 8px rgba(20,184,166,0.15), 0 0 28px rgba(20,184,166,0.45);
      display:flex;
      align-items:center;
      justify-content:center;
      color:white;
      font-size: 11px;
      font-weight: 700;
    ">D</div>
  `,
  iconSize: [22, 22],
  iconAnchor: [11, 11],
});

function stopIcon(index: number) {
  return divIcon({
    className: "",
    html: `
      <div style="
        width: 24px;
        height: 24px;
        border-radius: 9999px;
        background: linear-gradient(180deg, #38bdf8, #2563eb);
        border: 3px solid rgba(4, 17, 29, 0.96);
        box-shadow: 0 0 0 8px rgba(56,189,248,0.08);
        display:flex;
        align-items:center;
        justify-content:center;
        color:white;
        font-size: 11px;
        font-weight: 700;
      ">${index}</div>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
}

function MapClickLayer({ onMapClick }: { onMapClick: (latitude: number, longitude: number) => void }) {
  useMapEvents({
    click(event) {
      onMapClick(event.latlng.lat, event.latlng.lng);
    },
  });

  return null;
}

export function RoutePlannerMap({
  depot,
  stops,
  naiveRoute,
  optimizedRoutes,
  onMapClick,
}: {
  depot: [number, number];
  stops: PlannedStop[];
  naiveRoute: [number, number][];
  optimizedRoutes: OptimizedMapRoute[];
  onMapClick: (latitude: number, longitude: number) => void;
}) {
  return (
    <div className="overflow-hidden rounded-[2rem] border border-white/10 bg-white/5 shadow-glow backdrop-blur-xl">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 px-6 py-5">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Interactive map</p>
          <h2 className="mt-1 text-xl font-semibold text-white">Click to drop delivery stops</h2>
        </div>
        <div className="flex flex-wrap gap-2 text-xs text-slate-300">
          <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">Gray = naive route</span>
          <span className="rounded-full border border-sky-400/20 bg-sky-500/10 px-3 py-1">Color = optimized route</span>
        </div>
      </div>

      <MapContainer center={depot} zoom={5} scrollWheelZoom className="h-[620px] w-full">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapClickLayer onMapClick={onMapClick} />

        {naiveRoute.length > 1 ? (
          <Polyline positions={naiveRoute} pathOptions={{ color: "#94a3b8", weight: 4, opacity: 0.65, dashArray: "8 12" }} />
        ) : null}

        {optimizedRoutes.map((route) => (
          <Polyline key={route.id} positions={route.coordinates} pathOptions={{ color: route.color, weight: 4, opacity: 0.9 }} />
        ))}

        <Marker position={depot} icon={depotIcon}>
          <Popup>
            <div className="space-y-1">
              <p className="font-semibold">Control Tower depot</p>
              <p className="text-xs text-slate-500">Optimized routes start and end here.</p>
            </div>
          </Popup>
        </Marker>

        {stops.map((stop, index) => (
          <Marker key={stop.id} position={[stop.latitude, stop.longitude]} icon={stopIcon(index + 1)}>
            <Popup>
              <div className="space-y-1">
                <p className="font-semibold">{stop.name}</p>
                <p className="text-xs">Demand: {stop.demand}</p>
                <p className="text-xs text-slate-500">
                  {stop.latitude.toFixed(4)}, {stop.longitude.toFixed(4)}
                </p>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
