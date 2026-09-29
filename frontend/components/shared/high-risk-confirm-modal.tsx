import { AlertTriangle } from 'lucide-react';
import React from 'react';

interface HighRiskItem {
  id: string;
  label: string;
}

interface HighRiskConfirmModalProps {
  isOpen: boolean;
  highRiskItems: HighRiskItem[];
  onConfirm: () => void;
  onCancel: () => void;
}

export const HighRiskConfirmModal: React.FC<HighRiskConfirmModalProps> = ({
  isOpen,
  highRiskItems,
  onConfirm,
  onCancel,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center gap-3 mb-4 text-amber-600">
          <AlertTriangle className="w-6 h-6" />
          <h2 className="text-lg font-bold text-slate-900">High Risk Items Detected</h2>
        </div>
        <p className="text-sm text-slate-600 mb-4">
          The following items are flagged HIGH risk. Are you sure you want to approve them?
        </p>
        <ul className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-6 max-h-40 overflow-y-auto">
          {highRiskItems.map((item) => (
            <li key={item.id} className="text-xs font-mono text-amber-900 py-1 border-b border-amber-100 last:border-0 flex justify-between">
              <span>{item.label}</span>
              <span className="text-amber-600/70">#{item.id.slice(0, 8)}</span>
            </li>
          ))}
        </ul>
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100 rounded-lg"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="px-4 py-2 text-sm font-semibold text-white bg-amber-600 hover:bg-amber-700 rounded-lg"
          >
            Yes, Approve Anyway
          </button>
        </div>
      </div>
    </div>
  );
};
