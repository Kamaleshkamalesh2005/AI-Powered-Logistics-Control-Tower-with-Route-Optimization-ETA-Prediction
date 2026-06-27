import { useMemo, useState } from "react";

import type { ShipmentRow, ShipmentStatus } from "../types/dashboard";

const statusStyles: Record<ShipmentStatus, string> = {
  in_transit: "bg-sky-500/15 text-sky-300 ring-sky-400/30",
  delivered: "bg-emerald-500/15 text-emerald-300 ring-emerald-400/30",
  pending: "bg-amber-500/15 text-amber-300 ring-amber-400/30",
  exception: "bg-rose-500/15 text-rose-300 ring-rose-400/30",
};

const statusOptions: Array<ShipmentStatus | "all"> = ["all", "in_transit", "delivered", "pending", "exception"];

export function ShipmentTable({ shipments }: { shipments: ShipmentRow[] }) {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<ShipmentStatus | "all">("all");

  const filteredShipments = useMemo(() => {
    const query = search.trim().toLowerCase();
    return shipments.filter((shipment) => {
      const matchesSearch =
        query.length === 0 ||
        shipment.reference.toLowerCase().includes(query) ||
        shipment.customerName.toLowerCase().includes(query) ||
        shipment.origin.toLowerCase().includes(query) ||
        shipment.destination.toLowerCase().includes(query) ||
        shipment.vehicleId.toLowerCase().includes(query);
      const matchesStatus = status === "all" || shipment.status === status;
      return matchesSearch && matchesStatus;
    });
  }, [search, shipments, status]);

  return (
    <section className="rounded-[2rem] border border-white/10 bg-white/5 p-6 shadow-glow backdrop-blur-xl">
      <div className="mb-5 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Shipment table</p>
          <h2 className="mt-1 text-xl font-semibold text-white">Search and filter active freight</h2>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <label className="relative block">
            <span className="sr-only">Search shipments</span>
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search reference, origin, destination, vehicle..."
              className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-sky-400/40"
            />
          </label>
          <select
            value={status}
            onChange={(event) => setStatus(event.target.value as ShipmentStatus | "all")}
            className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-sky-400/40"
          >
            {statusOptions.map((option) => (
              <option key={option} value={option}>
                {option === "all" ? "All statuses" : option.replace("_", " ")}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="overflow-hidden rounded-3xl border border-white/10">
        <div className="grid grid-cols-[1.2fr_1.1fr_0.8fr_0.8fr_0.8fr_0.8fr] gap-4 border-b border-white/10 bg-white/5 px-5 py-4 text-xs uppercase tracking-[0.25em] text-slate-400">
          <div>Shipment</div>
          <div>Route</div>
          <div>Vehicle</div>
          <div>Status</div>
          <div>ETA</div>
          <div>Updated</div>
        </div>

        <div className="divide-y divide-white/10 bg-slate-950/40">
          {filteredShipments.map((shipment) => (
            <div key={shipment.id} className="grid grid-cols-[1.2fr_1.1fr_0.8fr_0.8fr_0.8fr_0.8fr] gap-4 px-5 py-4 text-sm text-slate-200">
              <div>
                <p className="font-semibold text-white">{shipment.reference}</p>
                <p className="mt-1 text-xs text-slate-400">{shipment.customerName}</p>
              </div>
              <div>
                <p>{shipment.origin}</p>
                <p className="mt-1 text-xs text-slate-400">to {shipment.destination}</p>
              </div>
              <div>{shipment.vehicleId}</div>
              <div>
                <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1 ${statusStyles[shipment.status]}`}>
                  {shipment.status.replace("_", " ")}
                </span>
              </div>
              <div>
                <p className="font-semibold text-white">{shipment.etaMinutes} min</p>
                <p className="mt-1 text-xs text-slate-400">{shipment.delayMinutes} min delay</p>
              </div>
              <div className="text-xs text-slate-400">{new Date(shipment.updatedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</div>
            </div>
          ))}

          {filteredShipments.length === 0 ? (
            <div className="px-5 py-10 text-center text-sm text-slate-400">No shipments match the current search and filter.</div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
