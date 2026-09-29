"use client";

import { RoleGuard } from "@/components/auth/role-guard";
import { useQuery } from "@tanstack/react-query";
import { paymentsApi } from "@/lib/api/payments";
import { MakerTaskPanel } from "@/components/dashboard/maker-task-panel";
import { useAuth } from "@/components/auth/auth-provider";

export default function MakerPage() {
  const { user } = useAuth();
  
  const { data: payments, isLoading, error } = useQuery({
    queryKey: ['maker-recent-payments', { limit: 8 }],
    queryFn: () => paymentsApi.getRecentPayments({ limit: 8 }),
    staleTime: 60 * 1000,
  });

  return (
    <RoleGuard allow={["MAKER"]}>
      <div className="space-y-6 max-w-5xl">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Welcome, {user?.email.split('@')[0]}</h1>
          <p className="text-sm text-gray-500 mt-1">Manage your active payment requests and vendor pipeline.</p>
        </div>

        <MakerTaskPanel 
          payments={payments || []} 
          isLoading={isLoading} 
          error={error as Error | null} 
        />
      </div>
    </RoleGuard>
  );
}