import { AlertTriangle } from 'lucide-react';
import React from 'react';

interface DivergenceWarningProps {
  ruleLevel: string;
  mlLevel: string | null;
  mlAvailable?: boolean;
}

export const DivergenceWarning: React.FC<DivergenceWarningProps> = ({
  ruleLevel,
  mlLevel,
  mlAvailable = true,
}) => {
  if (!mlAvailable || !mlLevel) return null;

  const rule = ruleLevel.toUpperCase();
  const ml = mlLevel.toUpperCase();

  const isDivergent =
    (rule === 'LOW' && ml === 'HIGH') ||
    (rule === 'HIGH' && ml === 'LOW');

  if (!isDivergent) return null;

  const message =
    rule === 'LOW' && ml === 'HIGH'
      ? 'Divergent risk signal: Rules evaluated LOW, but ML model flagged anomalous behavioral patterns.'
      : 'Divergent risk signal: Rules flagged HIGH risk, but ML evaluated transaction patterns within normal bounds.';

  return (
    <div className="relative group inline-flex items-center">
      <div className="flex items-center justify-center w-5 h-5 rounded-full bg-amber-100 text-amber-700 border border-amber-300 cursor-help transition-transform hover:scale-110">
        <AlertTriangle className="w-3 h-3 stroke-[2.5]" />
      </div>

      <div className="absolute left-1/2 bottom-full mb-2 -translate-x-1/2 hidden group-hover:flex flex-col items-center z-50 pointer-events-none w-64">
        <div className="bg-slate-900 text-slate-100 text-xs font-normal rounded-lg p-2.5 shadow-xl border border-slate-700 text-center leading-relaxed">
          {message}
        </div>
        <div className="w-2 h-2 bg-slate-900 rotate-45 -mt-1 border-r border-b border-slate-700" />
      </div>
    </div>
  );
};