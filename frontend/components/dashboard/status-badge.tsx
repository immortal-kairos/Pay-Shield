import { PaymentStatus } from "@/types/api";

export function StatusBadge({ status }: { status: PaymentStatus }) {
  const config: Record<string, string> = {
    APPROVED: "bg-green-100 text-green-800 border-green-200",
    REJECTED: "bg-red-100 text-red-800 border-red-200",
    PENDING_APPROVAL: "bg-amber-100 text-amber-800 border-amber-200",
  };

  const badgeClass = config[status] || "bg-gray-100 text-gray-800 border-gray-200";
  const label = status.replace("_", " ");

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${badgeClass}`}>
      {label}
    </span>
  );
}