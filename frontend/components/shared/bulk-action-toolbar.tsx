import { Loader2 } from 'lucide-react';
import React from 'react';

interface BulkActionToolbarProps {
  selectedCount: number;
  onApprove: () => void;
  onReject: () => void;
  onClear: () => void;
  isProcessing: boolean;
}

export const BulkActionToolbar: React.FC<BulkActionToolbarProps> = ({
  selectedCount,
  onApprove,
  onReject,
  onClear,
  isProcessing,
}) => {
  if (selectedCount === 0) return null;

  return (
    <div className="absolute bottom-0 left-0 right-0 p-3 bg-white border-t border-slate-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] flex items-center justify-between z-10">
      <div className="flex items-center gap-3 pl-2">
        <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 font-bold text-xs">
          {selectedCount}
        </span>
        <span className="text-sm font-medium text-slate-700">items selected</span>
        <button 
          onClick={onClear}
          disabled={isProcessing}
          className="text-xs text-slate-500 hover:text-slate-700 underline ml-2 disabled:opacity-50"
        >
          Clear Selection
        </button>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={onReject}
          disabled={isProcessing}
          className="px-4 py-2 text-sm font-semibold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 rounded-lg transition-colors disabled:opacity-50 flex items-center"
        >
          {isProcessing && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
          Reject Selected
        </button>
        <button
          onClick={onApprove}
          disabled={isProcessing}
          className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-colors disabled:opacity-50 flex items-center"
        >
          {isProcessing && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
          Approve Selected
        </button>
      </div>
    </div>
  );
};
