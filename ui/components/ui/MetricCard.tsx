export default function MetricCard({
    label,
    value,
    delta,
  }: {
    label: string;
    value: string | number;
    delta?: string;
  }) {
    return (
      <div className="rounded-2xl bg-white border border-slate-200 p-6 shadow-sm">
        <div className="h-11 w-11 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-5">
          ✦
        </div>
        <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
        <p className="text-3xl font-bold mt-2 text-slate-900">{value}</p>
        {delta && <p className="text-sm text-emerald-600 mt-2">{delta}</p>}
      </div>
    );
  }