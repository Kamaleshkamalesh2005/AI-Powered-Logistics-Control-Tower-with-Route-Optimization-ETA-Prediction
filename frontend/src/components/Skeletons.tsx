function baseClassName(className: string) {
  return `animate-pulse rounded-2xl bg-white/8 ${className}`;
}

export function KpiSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-4">
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className="rounded-3xl border border-white/10 bg-white/5 p-5">
          <div className={baseClassName("h-4 w-24")} />
          <div className={baseClassName("mt-4 h-9 w-28")} />
          <div className={baseClassName("mt-3 h-3 w-36")} />
        </div>
      ))}
    </div>
  );
}

export function MapSkeleton() {
  return <div className="h-[520px] rounded-[2rem] border border-white/10 bg-white/5 animate-pulse" />;
}

export function AnalyticsSkeleton() {
  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <div className="h-[320px] rounded-[2rem] border border-white/10 bg-white/5 animate-pulse" />
      <div className="h-[320px] rounded-[2rem] border border-white/10 bg-white/5 animate-pulse" />
    </div>
  );
}

export function TableSkeleton() {
  return (
    <div className="overflow-hidden rounded-[2rem] border border-white/10 bg-white/5">
      <div className="p-5">
        <div className={baseClassName("h-10 w-full")} />
      </div>
      <div className="space-y-3 px-5 pb-5">
        {Array.from({ length: 7 }).map((_, index) => (
          <div key={index} className="grid grid-cols-6 gap-4 rounded-2xl border border-white/8 bg-white/5 p-4">
            <div className={baseClassName("h-4 w-20")} />
            <div className={baseClassName("h-4 w-24")} />
            <div className={baseClassName("h-4 w-28")} />
            <div className={baseClassName("h-4 w-16")} />
            <div className={baseClassName("h-4 w-14")} />
            <div className={baseClassName("h-4 w-20")} />
          </div>
        ))}
      </div>
    </div>
  );
}

export function RoutePlannerSkeleton() {
  return (
    <div className="grid gap-6 xl:grid-cols-[1.35fr_0.95fr]">
      <div className="h-[620px] rounded-[2rem] border border-white/10 bg-white/5 animate-pulse" />
      <div className="space-y-4">
        <div className="h-[240px] rounded-[2rem] border border-white/10 bg-white/5 animate-pulse" />
        <div className="h-[160px] rounded-[2rem] border border-white/10 bg-white/5 animate-pulse" />
      </div>
    </div>
  );
}
