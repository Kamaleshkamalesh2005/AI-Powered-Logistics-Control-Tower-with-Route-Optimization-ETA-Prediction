import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { DelayCausePoint, DelayTrendPoint } from "../types/dashboard";

const causeColors = ["#60a5fa", "#f59e0b", "#34d399", "#f43f5e", "#a78bfa"];

export function AnalyticsPanel({ trend, causes }: { trend: DelayTrendPoint[]; causes: DelayCausePoint[] }) {
  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <section className="rounded-[2rem] border border-white/10 bg-white/5 p-6 shadow-glow backdrop-blur-xl">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Delay trend</p>
            <h2 className="mt-1 text-xl font-semibold text-white">Rolling delay minutes</h2>
          </div>
          <span className="rounded-full border border-sky-400/20 bg-sky-500/10 px-3 py-1 text-xs text-sky-200">Area chart</span>
        </div>

        <div className="h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trend}>
              <defs>
                <linearGradient id="delayGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.45} />
                  <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="4 4" stroke="rgba(148,163,184,0.16)" />
              <XAxis dataKey="period" stroke="#94a3b8" fontSize={12} />
              <YAxis stroke="#94a3b8" fontSize={12} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "rgba(4, 17, 29, 0.95)",
                  border: "1px solid rgba(148, 163, 184, 0.16)",
                  borderRadius: "16px",
                  color: "#e2e8f0",
                }}
              />
              <Area type="monotone" dataKey="delayMinutes" stroke="#38bdf8" strokeWidth={3} fill="url(#delayGradient)" />
              <Area type="monotone" dataKey="movingAverage" stroke="#a78bfa" strokeWidth={2} fillOpacity={0} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="rounded-[2rem] border border-white/10 bg-white/5 p-6 shadow-glow backdrop-blur-xl">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Delay breakdown</p>
            <h2 className="mt-1 text-xl font-semibold text-white">Cause distribution</h2>
          </div>
          <span className="rounded-full border border-amber-400/20 bg-amber-500/10 px-3 py-1 text-xs text-amber-200">Bar chart</span>
        </div>

        <div className="h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={causes}>
              <CartesianGrid strokeDasharray="4 4" stroke="rgba(148,163,184,0.16)" />
              <XAxis dataKey="cause" stroke="#94a3b8" fontSize={12} />
              <YAxis stroke="#94a3b8" fontSize={12} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "rgba(4, 17, 29, 0.95)",
                  border: "1px solid rgba(148, 163, 184, 0.16)",
                  borderRadius: "16px",
                  color: "#e2e8f0",
                }}
              />
              <Bar dataKey="count" radius={[10, 10, 0, 0]}>
                {causes.map((entry, index) => (
                  <Cell key={entry.cause} fill={causeColors[index % causeColors.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
}
