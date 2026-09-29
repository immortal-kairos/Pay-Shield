import { DivergenceWarning } from '@/components/payments/divergence-warning';
import { MLRiskBadge } from '@/components/payments/ml-risk-badge';
import { MLRiskDrawer } from '@/components/payments/ml-risk-drawer';
import { BulkActionToolbar } from '@/components/shared/bulk-action-toolbar';
import { BulkRejectModal } from '@/components/shared/bulk-reject-modal';
import { HighRiskConfirmModal } from '@/components/shared/high-risk-confirm-modal';
import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts';
import { useRowSelection } from '@/hooks/use-row-selection';
import { formatCurrency, formatDate } from '@/lib/utils/format';
import { Payment } from '@/types/api';
import {
  Building2,
  Calendar,
  CheckCircle2,
  Eye
} from 'lucide-react';
import React, { useState } from 'react';

interface PendingPaymentsTableProps {
  payments: Payment[];
  isLoading: boolean;
  onApprove: (paymentId: string) => Promise<void>;
  onReject: (paymentId: string, reason: string) => Promise<void>;
  onBulkApprove: (paymentIds: string[]) => Promise<void>;
  onBulkReject: (paymentIds: string[], reason: string) => Promise<void>;
}

export const PendingPaymentsTable: React.FC<PendingPaymentsTableProps> = ({
  payments,
  isLoading,
  onApprove,
  onReject,
  onBulkApprove,
  onBulkReject,
}) => {
  // Drawer State
  const [selectedPayment, setSelectedPayment] = useState<Payment | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  
  // Modals State
  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false);
  const [isHighRiskModalOpen, setIsHighRiskModalOpen] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  // --- 1. The Strict Selection Hook ---
  const availableIds = payments.map(p => p.id);
  const {
    selectedIds,
    toggle,
    toggleAll,
    clear,
    isSelected,
    isAllSelected,
  } = useRowSelection(availableIds);

  // Register Global Hotkeys
  useKeyboardShortcuts([
    {
      key: 'Escape',
      disabled: selectedIds.size === 0 || isDrawerOpen,
      handler: clear
    },
    {
      key: 'a',
      altKey: true,
      preventDefault: true,
      disabled: payments.length === 0 || isDrawerOpen,
      handler: toggleAll
    }
  ]);

  // --- 2. High-Risk Interception Logic ---
  const highRiskSelected = payments
    .filter(p => selectedIds.has(p.id) && (p.risk_level?.toUpperCase() === 'HIGH' || p.ml_risk_label?.toUpperCase() === 'HIGH'))
    .map(p => ({
      id: p.id,
      label: `${p.vendor_name || 'Vendor'} - ${formatCurrency(p.amount, p.currency)}`
    }));

  const handleInitiateApprove = () => {
    if (highRiskSelected.length > 0) {
      setIsHighRiskModalOpen(true); // Intercept the approval!
    } else {
      executeBulkApprove();
    }
  };

  // --- 3. Execution Wrappers ---
  const executeBulkApprove = async () => {
    setIsHighRiskModalOpen(false);
    setIsProcessing(true);
    try {
      const idsArray = Array.from(selectedIds);
      await onBulkApprove(idsArray);
      clear(); 
    } catch (error) {
      console.error("Bulk approve failed", error);
    } finally {
      setIsProcessing(false);
    }
  };

  const executeBulkReject = async (reason: string) => {
    setIsRejectModalOpen(false);
    setIsProcessing(true);
    try {
      const idsArray = Array.from(selectedIds);
      await onBulkReject(idsArray, reason);
      clear();
    } catch (error) {
      console.error("Bulk reject failed", error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleOpenInspect = (payment: Payment) => {
    setSelectedPayment(payment);
    setIsDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setIsDrawerOpen(false);
    setSelectedPayment(null);
  };

  if (isLoading) {
    return (
      <div className="w-full bg-white rounded-xl border border-slate-200 p-12 text-center">
        <div className="inline-block animate-spin w-8 h-8 border-4 border-slate-300 border-t-indigo-600 rounded-full mb-3" />
        <p className="text-sm font-medium text-slate-500">Loading pending audit ledger...</p>
      </div>
    );
  }

  if (payments.length === 0) {
    return (
      <div className="w-full bg-white rounded-xl border border-slate-200 p-12 text-center">
        <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-3">
          <CheckCircle2 className="w-6 h-6" />
        </div>
        <h3 className="text-base font-bold text-slate-800">Review Ledger Clean</h3>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          There are currently no payments awaiting checker sign-off.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="w-full bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden relative">
        <div className="overflow-x-auto pb-16">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                <th className="py-3.5 px-4 w-12">
                  <input 
                    type="checkbox" 
                    className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-600"
                    checked={isAllSelected}
                    onChange={toggleAll}
                  />
                </th>
                <th className="py-3.5 px-4">Payment ID & Vendor</th>
                <th className="py-3.5 px-4">Amount</th>
                <th className="py-3.5 px-4">Scheduled Date</th>
                <th className="py-3.5 px-4">Rule Risk</th>
                <th className="py-3.5 px-4">ML Anomaly Risk</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
              {payments.map((payment) => {
                const ruleLevel = payment.risk_level?.toUpperCase() || 'LOW';
                const mlLevel = payment.ml_risk_label?.toUpperCase() || null;
                const isRowSelected = isSelected(payment.id);

                const isDivergent =
                  payment.ml_available &&
                  ((ruleLevel === 'LOW' && mlLevel === 'HIGH') ||
                    (ruleLevel === 'HIGH' && mlLevel === 'LOW'));

                const rowBgClass = isRowSelected 
                  ? 'bg-indigo-50/60'
                  : isDivergent
                    ? 'bg-amber-50/40 hover:bg-amber-50/70'
                    : 'hover:bg-slate-50/80';

                return (
                  <tr key={payment.id} className={`transition-colors ${rowBgClass}`}>
                    <td className="py-3 px-4">
                      <input 
                        type="checkbox" 
                        className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-600"
                        checked={isRowSelected}
                        onChange={() => toggle(payment.id)}
                      />
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900 flex items-center gap-1.5">
                        <Building2 className="w-3.5 h-3.5 text-slate-400" />
                        {payment.vendor_name || 'Vendor Account'}
                      </div>
                      <div className="text-[11px] font-mono text-slate-400 mt-0.5">
                        #{payment.id.slice(0, 8)}
                      </div>
                    </td>
                    <td className="py-3 px-4 font-semibold text-slate-900">
                      {formatCurrency(payment.amount, payment.currency)}
                    </td>
                    <td className="py-3 px-4 text-slate-600">
                      <div className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        {formatDate(payment.payment_date || payment.execution_date || '')}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                          ruleLevel === 'HIGH'
                            ? 'bg-rose-50 text-rose-700 border-rose-200'
                            : ruleLevel === 'MEDIUM'
                            ? 'bg-amber-50 text-amber-700 border-amber-200'
                            : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        }`}
                      >
                        {ruleLevel} ({Math.round(payment.risk_score || 0)})
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <MLRiskBadge
                          mlRiskScore={payment.ml_risk_score}
                          mlRiskLabel={payment.ml_risk_label as string}
                          mlAvailable={payment.ml_available}
                          size="sm"
                        />
                        <DivergenceWarning
                          ruleLevel={ruleLevel}
                          mlLevel={mlLevel}
                          mlAvailable={payment.ml_available}
                        />
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => handleOpenInspect(payment)}
                          className="px-2.5 py-1.5 text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 hover:bg-indigo-100 rounded-lg transition-colors flex items-center gap-1"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          Inspect Risk
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* 4. The Shared Toolbar Component */}
        <BulkActionToolbar
          selectedCount={selectedIds.size}
          onApprove={handleInitiateApprove}
          onReject={() => setIsRejectModalOpen(true)}
          onClear={clear}
          isProcessing={isProcessing}
        />
      </div>

      {/* 5. The strict Rejection Reason Modal */}
      <BulkRejectModal
        isOpen={isRejectModalOpen}
        selectedCount={selectedIds.size}
        onSubmit={executeBulkReject}
        onCancel={() => setIsRejectModalOpen(false)}
      />

      {/* 6. The High-Risk Interceptor Modal */}
      <HighRiskConfirmModal
        isOpen={isHighRiskModalOpen}
        highRiskItems={highRiskSelected}
        onConfirm={executeBulkApprove}
        onCancel={() => setIsHighRiskModalOpen(false)}
      />

      {/* Existing Slide-over Drawer */}
      <MLRiskDrawer
        payment={selectedPayment}
        isOpen={isDrawerOpen}
        onClose={handleCloseDrawer}
        onApprove={onApprove}
        onReject={onReject}
      />
    </>
  );
};