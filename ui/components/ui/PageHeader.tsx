export default function PageHeader({
    label,
    title,
    description,
  }: {
    label: string;
    title: string;
    description: string;
  }) {
    return (
      <div className="mb-10">
        <p className="text-sm uppercase tracking-widest text-indigo-600 font-semibold">
          {label}
        </p>
        <h1 className="text-5xl font-bold text-slate-950 mt-2">{title}</h1>
        <p className="text-slate-500 mt-3 max-w-3xl">{description}</p>
      </div>
    );
  }