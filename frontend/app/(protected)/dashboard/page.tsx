"use client";

import { RoleGuard } from "@/components/auth/role-guard";
import { DashboardSkeleton } from "@/components/dashboard/dashboard-skeleton";
import { RecentPaymentsTable } from "@/components/dashboard/recent-payments-table";
import { StatCard } from "@/components/dashboard/stat-card";
import { TopVendorsCard } from "@/components/dashboard/top-vendors-card";
import { analyticsApi } from "@/lib/api/analytics";
import { paymentsApi } from "@/lib/api/payments";
import { formatCompactNumber } from "@/lib/utils/format";
import { useQuery } from "@tanstack/react-query";

export default function DashboardPage() {
  const { data: metrics, isLoading: metricsLoading, error: metricsError } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: analyticsApi.getDashboardMetrics,
    staleTime: 60 * 1000, // 1 minute
  });

  const { data: payments, isLoading: paymentsLoading, error: paymentsError } = useQuery({
    queryKey: ['recent-payments', { limit: 5 }],
    queryFn: () => paymentsApi.getRecentPayments({ limit: 5 }),
    staleTime: 60 * 1000,
  });

  if (metricsLoading) {
    return (
      <RoleGuard allow={["ADMIN", "CHECKER"]}>
        <DashboardSkeleton />
      </RoleGuard>
    );
  }

  if (metricsError) {
    return (
      <RoleGuard allow={["ADMIN", "CHECKER"]}>
        <div className="p-8 bg-red-50 text-red-700 rounded-xl border border-red-200">
          <h2 className="text-xl font-bold mb-2">Analytics Unavailable</h2>
          <p>We encountered an error loading the executive dashboard. Please try again later.</p>
        </div>
      </RoleGuard>
    );
  }

  return (
    <RoleGuard allow={["ADMIN", "CHECKER"]}>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Executive Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">Real-time payment flow and risk overview.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard 
            title="Total Processed Volume" 
            value={`₹${formatCompactNumber(metrics?.total_volume || 0)}`} 
            tone="default"
          />
          <StatCard 
            title="Pending Approval" 
            value={metrics?.pending_count || 0} 
            tone="warning"
            subtitle="Requires Checker Action"
          />
          <StatCard 
            title="High Risk Detected" 
            value={metrics?.high_risk_count || 0} 
            tone="danger"
            subtitle="Immediate Review Suggested"
          />
          <StatCard 
            title="Approved Transactions" 
            value={metrics?.approved_count || 0} 
            tone="success"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <h2 className="text-lg font-bold text-gray-900">Recent Transactions</h2>
            <RecentPaymentsTable payments={payments || []} isLoading={paymentsLoading} error={paymentsError as Error | null} />
          </div>
          <div className="space-y-4">
            <TopVendorsCard vendors={metrics?.top_vendors || []} />
          </div>
        </div>
      </div>
    </RoleGuard>
  );
}