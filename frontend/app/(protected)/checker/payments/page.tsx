'use client';

import { RoleGuard } from '@/components/auth/role-guard';
import { PendingPaymentsTable } from '@/components/payments/pending-payments-table';
import {
  approvePayment,
  bulkApprovePayments,
  bulkRejectPayments,
  getPendingPayments,
  rejectPayment,
} from '@/lib/api/payments';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { RefreshCw, ShieldAlert } from 'lucide-react';
import { useTransition } from 'react';

export default function CheckerPaymentsPage() {
  const queryClient = useQueryClient();
  const [isPending, startTransition] = useTransition();

  const {
    data: payments = [],
    isLoading,
    isRefetching,
    refetch,
    error,
  } = useQuery({
    queryKey: ['payments', 'pending'],
    queryFn: getPendingPayments,
    staleTime: 1000 * 30,
  });

  const approveMutation = useMutation({
    mutationFn: (paymentId: string) => approvePayment(paymentId),
    onSuccess: () => {
      startTransition(() => {
        queryClient.invalidateQueries({ queryKey: ['payments', 'pending'] });
      });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ paymentId, reason }: { paymentId: string; reason: string }) =>
      rejectPayment(paymentId, { rejection_reason: reason }),
    onSuccess: () => {
      startTransition(() => {
        queryClient.invalidateQueries({ queryKey: ['payments', 'pending'] });
      });
    },
  });

  const bulkApproveMutation = useMutation({
    mutationFn: (paymentIds: string[]) => bulkApprovePayments(paymentIds),
    onSuccess: () => {
      startTransition(() => {
        queryClient.invalidateQueries({ queryKey: ['payments', 'pending'] });
      });
    },
  });

  const bulkRejectMutation = useMutation({
    mutationFn: ({ paymentIds, reason }: { paymentIds: string[]; reason: string }) =>
      bulkRejectPayments(paymentIds, reason),
    onSuccess: () => {
      startTransition(() => {
        queryClient.invalidateQueries({ queryKey: ['payments', 'pending'] });
      });
    },
  });

  const handleApprove = async (paymentId: string) => {
    await approveMutation.mutateAsync(paymentId);
  };

  const handleReject = async (paymentId: string, reason: string) => {
    await rejectMutation.mutateAsync({ paymentId, reason });
  };

  // THE FIX: explicitly return the API response data so the table can read failed_count
  const handleBulkApprove = async (paymentIds: string[]) => {
    return await bulkApproveMutation.mutateAsync(paymentIds);
  };

  const handleBulkReject = async (paymentIds: string[], reason: string) => {
    return await bulkRejectMutation.mutateAsync({ paymentIds, reason });
  };

  return (
    <RoleGuard allow={['CHECKER', 'ADMIN']}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              Payment Approval Ledger
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Evaluate rules and machine learning anomaly tensors prior to signing off disbursements.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => refetch()}
              disabled={isLoading || isRefetching}
              className="px-3.5 py-2 text-xs font-bold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg shadow-sm transition-all flex items-center gap-1.5 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefetching ? 'animate-spin' : ''}`} />
              Refresh Queue
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-sm">
            <ShieldAlert className="w-5 h-5 shrink-0 mt-0.5 text-rose-600" />
            <div>
              <h3 className="font-bold">Failed to load payment queue</h3>
              <p className="text-xs text-rose-700 mt-0.5">
                {(error as any)?.message || 'An error occurred communicating with the PayShield API.'}
              </p>
            </div>
          </div>
        )}

        <PendingPaymentsTable
          payments={payments}
          isLoading={isLoading}
          onApprove={handleApprove}
          onReject={handleReject}
          onBulkApprove={handleBulkApprove}
          onBulkReject={handleBulkReject}
        />
      </div>
    </RoleGuard>
  );
}