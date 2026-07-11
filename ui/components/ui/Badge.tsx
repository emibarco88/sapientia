export default function Badge({
    children,
    tone = "indigo",
  }: {
    children: React.ReactNode;
    tone?: "indigo" | "green" | "slate" | "amber" | "red";
  }) {
    const tones = {
      indigo: "bg-indigo-50 text-indigo-700",
      green: "bg-emerald-50 text-emerald-700",
      slate: "bg-slate-100 text-slate-700",
      amber: "bg-amber-50 text-amber-700",
      red: "bg-red-50 text-red-700",
    };
  
    return (
      <span className={`rounded-full px-3 py-1 text-xs font-medium ${tones[tone]}`}>
        {children}
      </span>
    );
  }