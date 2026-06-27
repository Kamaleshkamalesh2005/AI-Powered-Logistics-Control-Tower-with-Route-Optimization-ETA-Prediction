import type { KpiSummary } from "../types/dashboard";

const kpiCards = [
  {
    label: "On-time %",
    formatter: (value: number) => `${value.toFixed(1)}%`,
    tone: "from-emerald-500/20 to-emerald-500/5",
    accent: "text-emerald-300",
  },
  {
    label: "Avg delay",
    formatter: (value: number) => `${value.toFixed(1)} min`,
    tone: "from-amber-500/20 to-amber-500/5",
    accent: "text-amber-300",
  },
  {
    label: "Active shipments",
    formatter: (value: number) => `${value}`,
    tone: "from-sky-500/20 to-sky-500/5",
    accent: "text-sky-300",
  },
  {
    label: "Exception queue",
    formatter: (value: number) => `${value}`,
    tone: "from-rose-500/20 to-rose-500/5",
    accent: "text-rose-300",
  },
];

export function KpiStrip({ kpis }: { kpis: KpiSummary }) {
  const values = [kpis.onTimePercentage, kpis.averageDelayMinutes, kpis.activeShipments, kpis.exceptionQueue];

  return (
    <div className="grid gap-4 md:grid-cols-4">
      {kpiCards.map((card, index) => (
        <div key={card.label} className={`rounded-3xl border border-white/10 bg-gradient-to-br ${card.tone} p-5 shadow-glow`}>
          <p className="text-xs uppercase tracking-[0.28em] text-slate-400">{card.label}</p>
          <p className={`mt-3 text-3xl font-semibold ${card.accent}`}>{card.formatter(values[index])}</p>
          <p className="mt-2 text-sm text-slate-300">
            {index === 0 && "Shipment SLA compliance across the live network."}
            {index === 1 && "Across the last rolling 24-hour window."}
            {index === 2 && "Currently moving or awaiting handoff."}
            {index === 3 && "Requires dispatcher attention."}
          </p>
        </div>
      ))}
    </div>
  );
}
