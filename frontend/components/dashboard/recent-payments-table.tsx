"use client";

import { formatCurrencyINR, formatDate } from "@/lib/utils/format";
import { PaymentListItem } from "@/types/api";
import { EmptyState } from "./empty-state";
import { RiskBadge } from "./risk-badge";
import { StatusBadge } from "./status-badge";

export function RecentPaymentsTable({ payments, isLoading, error }: { payments: PaymentListItem[], isLoading: boolean, error: Error | null }) {
  if (error) {
    return (
      <div className="bg-red-50 p-6 rounded-xl border border-red-100 text-center">
        <p className="text-red-600 font-medium">Failed to load recent payments.</p>
      </div>
    );
  }

  if (isLoading) {
    return <div className="h-64 bg-gray-50 rounded-xl animate-pulse"></div>;
  }

  if (!payments || payments.length === 0) {
    return <EmptyState title="No recent payments" description="Payments requiring your attention will appear here." />;
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-100 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Vendor</th>
            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Amount</th>
            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Date</th>
            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Risk</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-100">
          {payments.map((payment) => (
            <tr key={payment.id} className="hover:bg-gray-50 transition-colors">
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {payment.vendor_name || 'Unknown Vendor'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {formatCurrencyINR(payment.amount)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {formatDate(payment.payment_date || payment.created_at)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <StatusBadge status={payment.status} />
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <RiskBadge risk={payment.risk_level} score={payment.risk_score} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
