interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  tone?: "default" | "success" | "warning" | "danger";
}

export function StatCard({ title, value, subtitle, tone = "default" }: StatCardProps) {
  const toneColors = {
    default: "text-blue-600",
    success: "text-emerald-600",
    warning: "text-amber-600",
    danger: "text-red-600",
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col">
      <h3 className="text-sm font-medium text-gray-500 mb-1">{title}</h3>
      <div className={`text-3xl font-bold tracking-tight ${toneColors[tone]}`}>
        {value}
      </div>
      {subtitle && <p className="text-xs text-gray-400 mt-2 font-medium">{subtitle}</p>}
    </div>
  );
}