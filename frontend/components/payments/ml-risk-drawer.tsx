import React, { useState } from 'react';
import {
  X,
  ShieldCheck,
  Cpu,
  CheckCircle2,
  XCircle,
  AlertOctagon,
  AlertTriangle,
  FileSpreadsheet,
  Info,
} from 'lucide-react';
import { Payment } from '@/types/api';
import { MLRiskBadge } from '@/components/payments/ml-risk-badge';
import {
  formatCurrency,
  formatDate,
  formatFeatureLabel,
  describeFeatureValue,
} from '@/lib/utils/format';

interface MLRiskDrawerProps {
  payment: Payment | null;
  isOpen: boolean;
  onClose: () => void;
  onApprove: (paymentId: string) => Promise<void>;
  onReject: (paymentId: string, reason: string) => Promise<void>;
}

export const MLRiskDrawer: React.FC<MLRiskDrawerProps> = ({
  payment,
  isOpen,
  onClose,
  onApprove,
  onReject,
}) => {
  const [rejectionReason, setRejectionReason] = useState('');
  const [isRejecting, setIsRejecting] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isOpen || !payment) return null;

  const handleApprove = async () => {
    try {
      setErrorMessage(null);
      setActionLoading(true);
      await onApprove(payment.id);
      onClose();
    } catch (err: any) {
      setErrorMessage(err?.response?.data?.detail || err?.message || 'Failed to approve payment.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRejectSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rejectionReason.trim().length < 5) {
      setErrorMessage('Rejection reason must be at least 5 characters long.');
      return;
    }

    try {
      setErrorMessage(null);
      setActionLoading(true);
      await onReject(payment.id, rejectionReason.trim());
      setIsRejecting(false);
      setRejectionReason('');
      onClose();
    } catch (err: any) {
      setErrorMessage(err?.response?.data?.detail || err?.message || 'Failed to reject payment.');
    } finally {
      setActionLoading(false);
    }
  };

  const snapshotEntries = payment.ml_feature_snapshot
    ? Object.entries(payment.ml_feature_snapshot)
    : [];

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-2xl bg-white shadow-2xl flex flex-col border-l border-slate-200">
          
          {/* Header */}
          <div className="p-6 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-slate-900">
                  Risk Intelligence Breakdown
                </h2>
                <span className="px-2 py-0.5 rounded text-xs font-mono font-semibold bg-slate-200 text-slate-700">
                  #{payment.id.slice(0, 8)}
                </span>
              </div>
              <p className="text-sm text-slate-500 mt-1">
                Vendor: <span className="font-medium text-slate-800">{payment.vendor_name || 'Vendor Account'}</span> • Scheduled Date: {formatDate(payment.payment_date || payment.execution_date || '')}
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 rounded-full transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Drawer Body */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            
            {/* Inline Error Toast */}
            {errorMessage && (
              <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-sm">
                <AlertOctagon className="w-5 h-5 shrink-0 mt-0.5 text-rose-600" />
                <div className="flex-1">
                  <p className="font-semibold">Action Failed</p>
                  <p className="mt-0.5 text-xs text-rose-700">{errorMessage}</p>
                </div>
              </div>
            )}

            {/* Offline Alert */}
            {!payment.ml_available && (
              <div className="p-4 rounded-xl bg-slate-100 border border-slate-300 flex items-start gap-3 text-slate-700 text-sm">
                <Info className="w-5 h-5 shrink-0 mt-0.5 text-slate-500" />
                <div>
                  <p className="font-semibold text-slate-800">ML Scoring Offline</p>
                  <p className="text-xs text-slate-600 mt-0.5">
                    ML Anomaly scoring is currently operating in offline mode. Base rules remain fully enforced.
                  </p>
                </div>
              </div>
            )}

            {/* Overall Evaluation Scorecards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              
              {/* Card 1: Rule Engine */}
              <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-sm hover:shadow transition-shadow">
                <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                  <div className="flex items-center gap-2 text-slate-700 font-semibold text-sm">
                    <ShieldCheck className="w-4 h-4 text-indigo-600" />
                    Rule-Based Risk Engine
                  </div>
                  <span className="text-xs font-mono text-slate-400 font-medium">AUTHORITATIVE</span>
                </div>
                <div className="mt-3 flex items-baseline justify-between">
                  <div>
                    <span className="text-3xl font-extrabold text-slate-900">
                      {Math.round(payment.risk_score)}
                    </span>
                    <span className="text-slate-400 text-sm font-medium"> / 100</span>
                  </div>
                  <span
                    className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                      payment.risk_level === 'HIGH'
                        ? 'bg-rose-100 text-rose-800'
                        : payment.risk_level === 'MEDIUM'
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-emerald-100 text-emerald-800'
                    }`}
                  >
                    {payment.risk_level}
                  </span>
                </div>
                <div className="mt-2 text-xs text-slate-500">
                  {payment.risk_flags && payment.risk_flags.length > 0
                    ? `Triggered ${payment.risk_flags.length} compliance rules`
                    : 'All static compliance parameters verified'}
                </div>
              </div>

              {/* Card 2: ML Isolation Forest */}
              <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-sm hover:shadow transition-shadow">
                <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                  <div className="flex items-center gap-2 text-slate-700 font-semibold text-sm">
                    <Cpu className="w-4 h-4 text-purple-600" />
                    ML Anomaly Engine
                  </div>
                  <span className="text-xs font-mono text-slate-400 font-medium">ISOLATION FOREST</span>
                </div>
                <div className="mt-3 flex items-baseline justify-between">
                  {payment.ml_available && payment.ml_risk_score !== null ? (
                    <>
                      <div>
                        <span className="text-3xl font-extrabold text-slate-900">
                          {Math.round(payment.ml_risk_score)}
                        </span>
                        <span className="text-slate-400 text-sm font-medium"> / 100</span>
                      </div>
                      <MLRiskBadge
                        mlRiskScore={payment.ml_risk_score}
                        mlRiskLabel={payment.ml_risk_label as string}
                        mlAvailable={payment.ml_available}
                      />
                    </>
                  ) : (
                    <div className="text-sm font-medium text-slate-400 italic py-1">
                      No ML Score Recorded
                    </div>
                  )}
                </div>
                <div className="mt-2 text-xs text-slate-500">
                  Calculated against 15 dimensional historical tensors
                </div>
              </div>
            </div>

            {/* Feature Contributions Section */}
            <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-sm">
              <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileSpreadsheet className="w-4 h-4 text-slate-600" />
                  <h3 className="font-bold text-slate-800 text-sm">
                    Engineered Feature Vector Snapshot (15 Signals)
                  </h3>
                </div>
                <span className="text-xs text-slate-500 font-medium">
                  {snapshotEntries.length} Features Recorded
                </span>
              </div>

              {snapshotEntries.length === 0 ? (
                <div className="p-8 text-center text-sm text-slate-500">
                  Feature snapshot not available for this payment record.
                </div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {snapshotEntries.map(([key, rawValue]) => {
                    const { displayValue, highlight } = describeFeatureValue(
                      key,
                      rawValue as number,
                      payment.currency
                    );

                    let badgeColor = 'bg-slate-100 text-slate-700 border-slate-200';
                    if (highlight === 'danger') {
                      badgeColor = 'bg-rose-50 text-rose-700 border-rose-200 font-bold';
                    } else if (highlight === 'warning') {
                      badgeColor = 'bg-amber-50 text-amber-800 border-amber-200 font-semibold';
                    }

                    return (
                      <div
                        key={key}
                        className="px-4 py-3 flex items-center justify-between hover:bg-slate-50/70 transition-colors"
                      >
                        <div className="text-xs font-medium text-slate-700 max-w-[280px]">
                          {formatFeatureLabel(key)}
                          <span className="block text-[10px] font-mono text-slate-400">
                            {key}
                          </span>
                        </div>

                        <div className="text-right">
                          <span
                            className={`inline-block px-2.5 py-1 rounded-md text-xs border ${badgeColor}`}
                          >
                            {displayValue}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Rejection Form Input Container */}
            {isRejecting && (
              <form
                onSubmit={handleRejectSubmit}
                className="p-4 rounded-xl border border-rose-200 bg-rose-50/40 space-y-3"
              >
                <div className="flex items-center gap-2 text-rose-800 font-bold text-sm">
                  <AlertTriangle className="w-4 h-4" />
                  Confirm Payment Rejection
                </div>
                <p className="text-xs text-rose-700 leading-relaxed">
                  Provide a mandatory audit reason explaining why this payment is being rejected. The Maker will be notified.
                </p>
                <textarea
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  placeholder="E.g., High ML anomaly score: 14.2x vendor historical amount spike on a newly registered entity."
                  rows={3}
                  disabled={actionLoading}
                  className="w-full text-xs p-2.5 border rounded-lg border-rose-300 focus:outline-none focus:ring-2 focus:ring-rose-500 bg-white"
                  required
                />
                <div className="flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setIsRejecting(false);
                      setRejectionReason('');
                    }}
                    disabled={actionLoading}
                    className="px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-200/60 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={actionLoading || rejectionReason.trim().length < 5}
                    className="px-4 py-1.5 text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 disabled:opacity-50 rounded-lg shadow-sm transition-colors"
                  >
                    {actionLoading ? 'Rejecting...' : 'Confirm Rejection'}
                  </button>
                </div>
              </form>
            )}
          </div>

          {/* Footer Actions */}
          {!isRejecting && (
            <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between gap-3">
              <button
                type="button"
                onClick={() => setIsRejecting(true)}
                disabled={actionLoading}
                className="px-4 py-2.5 text-xs font-bold text-rose-700 bg-rose-50 border border-rose-200 hover:bg-rose-100 hover:border-rose-300 rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50"
              >
                <XCircle className="w-4 h-4" />
                Reject Payment
              </button>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={actionLoading}
                  className="px-4 py-2.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 rounded-lg transition-colors disabled:opacity-50"
                >
                  Close
                </button>
                <button
                  type="button"
                  onClick={handleApprove}
                  disabled={actionLoading}
                  className="px-5 py-2.5 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm transition-colors flex items-center gap-1.5 disabled:opacity-50"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  {actionLoading ? 'Approving...' : 'Approve Payment'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};