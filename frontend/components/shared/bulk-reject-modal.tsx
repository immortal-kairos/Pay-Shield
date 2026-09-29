import React, { useState } from 'react';

interface BulkRejectModalProps {
  isOpen: boolean;
  selectedCount: number;
  onSubmit: (reason: string) => void;
  onCancel: () => void;
}

export const BulkRejectModal: React.FC<BulkRejectModalProps> = ({
  isOpen,
  selectedCount,
  onSubmit,
  onCancel,
}) => {
  const [reason, setReason] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (reason.trim().length >= 5) {
      onSubmit(reason);
      setReason(''); // Reset on submit
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <h2 className="text-lg font-bold text-slate-900 mb-2">Reject {selectedCount} Items</h2>
        <p className="text-sm text-slate-500 mb-4">
          Please provide a reason for rejecting these items. This will be logged in the audit trail.
        </p>
        <form onSubmit={handleSubmit}>
          <textarea
            autoFocus
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Reason for rejection (min 5 characters)..."
            className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rose-500 focus:border-rose-500 text-sm mb-4"
            rows={4}
          />
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={reason.trim().length < 5}
              className="px-4 py-2 text-sm font-semibold text-white bg-rose-600 hover:bg-rose-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Confirm Rejection
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};