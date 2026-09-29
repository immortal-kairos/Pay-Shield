import { RiskLevel } from "@/types/api";
import { AlertTriangle } from "lucide-react";

export function RiskBadge({ risk, score }: { risk: RiskLevel; score?: number }) {
  if (risk === "HIGH") {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-50 text-red-700 border border-red-200">
        <AlertTriangle size={12} />
        HIGH RISK {score ? `(${score})` : ""}
      </span>
    );
  }

  const badgeClass = risk === "MEDIUM" 
    ? "bg-yellow-50 text-yellow-700 border-yellow-200" 
    : "bg-emerald-50 text-emerald-700 border-emerald-200";

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${badgeClass}`}>
      {risk}
    </span>
  );
}