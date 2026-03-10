export function StatCard({
  icon,
  label,
  value,
  textColor,
  bgClass,
}: {
  icon: string;
  label: string;
  value: number | string;
  textColor: string;
  bgClass: string;
}) {
  return (
    <div className={`rounded-xl border p-4 text-center ${bgClass}`}>
      <div className="text-2xl mb-2">{icon}</div>
      <div className={`text-2xl font-bold ${textColor}`}>{value}</div>
      <div className="text-xs text-gray-500 mt-1 font-medium leading-tight">{label}</div>
    </div>
  );
}

export function MiniStat({ label, value, highlight = false }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div
      className={`rounded-lg p-3 text-center border ${
        highlight ? 'bg-primary-50 border-primary-200' : 'bg-cream-100 border-cream-300'
      }`}
    >
      <div className={`text-xl font-bold ${highlight ? 'text-primary-600' : 'text-dark'}`}>{value}</div>
      <div className="text-xs text-gray-500 mt-0.5">{label}</div>
    </div>
  );
}
