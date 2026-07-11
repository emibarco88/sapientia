export default function Panel({
    title,
    subtitle,
    children,
  }: {
    title: string;
    subtitle?: string;
    children: React.ReactNode;
  }) {
    return (
      <section className="rounded-3xl bg-white border border-slate-200 p-6 shadow-sm">
        <div className="mb-5">
          <h2 className="text-xl font-bold text-slate-950">{title}</h2>
          {subtitle && <p className="text-sm text-slate-500 mt-1">{subtitle}</p>}
        </div>
        {children}
      </section>
    );
  }