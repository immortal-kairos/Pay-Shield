import React from 'react';

interface MLRiskBadgeProps {
  mlRiskScore: number | null;
  mlRiskLabel: string | null;
  mlAvailable: boolean;
  size?: 'sm' | 'md';
}

export const MLRiskBadge: React.FC<MLRiskBadgeProps> = ({
  mlRiskScore,
  mlRiskLabel,
  mlAvailable,
  size = 'md',
}) => {
  if (!mlAvailable) {
    return (
      <span
        title="ML Anomaly Engine is currently offline or running in fallback mode"
        className={`inline-flex items-center gap-1.5 rounded-full font-medium border bg-slate-100 text-slate-600 border-slate-200 ${
          size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs'
        }`}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
        ML Inactive
      </span>
    );
  }

  if (mlRiskScore === null) {
    return (
      <span
        className={`inline-flex items-center rounded-full font-medium border bg-gray-50 text-gray-500 border-gray-200 ${
          size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs'
        }`}
      >
        N/A
      </span>
    );
  }

  const score = Math.round(mlRiskScore);
  const label = (mlRiskLabel || (score >= 70 ? 'HIGH' : score >= 40 ? 'MEDIUM' : 'LOW')).toUpperCase();

  let badgeStyles = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  let dotColor = 'bg-emerald-500';
  let meterTrackColor = 'bg-emerald-200';
  let meterFillColor = 'bg-emerald-600';

  if (score >= 70) {
    badgeStyles = 'bg-rose-50 text-rose-700 border-rose-200';
    dotColor = 'bg-rose-500';
    meterTrackColor = 'bg-rose-200';
    meterFillColor = 'bg-rose-600';
  } else if (score >= 40) {
    badgeStyles = 'bg-amber-50 text-amber-700 border-amber-200';
    dotColor = 'bg-amber-500';
    meterTrackColor = 'bg-amber-200';
    meterFillColor = 'bg-amber-600';
  }

  return (
    <div
      title={`Machine Learning Anomaly Score: ${score}/100 (${label})`}
      className={`inline-flex items-center gap-2 rounded-full border font-semibold tracking-tight shadow-sm ${badgeStyles} ${
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs'
      }`}
    >
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotColor}`} />
      <span>{label}</span>
      <span className="font-mono opacity-85">({score})</span>
      <div className={`w-8 h-1.5 rounded-full overflow-hidden shrink-0 ${meterTrackColor}`}>
        <div
          className={`h-full rounded-full ${meterFillColor}`}
          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
        />
      </div>
    </div>
  );
};