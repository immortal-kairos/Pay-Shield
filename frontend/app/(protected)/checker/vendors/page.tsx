"use client";

import { RoleGuard } from "@/components/auth/role-guard";
import { EmptyState } from "@/components/dashboard/empty-state";
import { PendingVendorsTable } from "@/components/vendors/pending-vendors-table";
import { VendorQueueSkeleton } from "@/components/vendors/vendor-queue-skeleton";
import { vendorsApi } from "@/lib/api/vendors";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useTransition } from "react";

export default function CheckerVendorQueuePage() {
  const queryClient = useQueryClient();
  const [isPending, startTransition] = useTransition();

  const { data: vendors, isLoading, error, refetch } = useQuery({
    queryKey: ["pending-vendors"],
    queryFn: vendorsApi.getPendingVendors,
  });

  // --- Bulk Action Mutations ---
  const bulkApproveMutation = useMutation({
    mutationFn: (vendorIds: string[]) => vendorsApi.bulkApproveVendors(vendorIds),
    onSuccess: () => {
      startTransition(() => {
        queryClient.invalidateQueries({ queryKey: ["pending-vendors"] });
      });
    },
  });

  const bulkRejectMutation = useMutation({
    mutationFn: ({ vendorIds, reason }: { vendorIds: string[]; reason: string }) =>
      vendorsApi.bulkRejectVendors(vendorIds, reason),
    onSuccess: () => {
      startTransition(() => {
        queryClient.invalidateQueries({ queryKey: ["pending-vendors"] });
      });
    },
  });

  // --- Handlers ---
  const handleBulkApprove = async (vendorIds: string[]) => {
    await bulkApproveMutation.mutateAsync(vendorIds);
  };

  const handleBulkReject = async (vendorIds: string[], reason: string) => {
    await bulkRejectMutation.mutateAsync({ vendorIds, reason });
  };

  return (
    <RoleGuard allow={["CHECKER"]}>
      <div className="space-y-6 max-w-5xl">
        <div>
          <Link href="/checker" className="inline-flex items-center text-sm font-medium text-blue-600 hover:text-blue-800 mb-4 transition-colors">
            <ArrowLeft size={16} className="mr-1" /> Back to Dashboard
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Vendor Approval Queue</h1>
          <p className="text-sm text-gray-500 mt-1">Review and action new vendor registrations submitted by makers.</p>
        </div>

        {error ? (
          <div className="p-6 bg-red-50 rounded-xl border border-red-200 flex items-center justify-between">
            <p className="text-red-700 font-medium">Failed to load the pending queue.</p>
            <button onClick={() => refetch()} className="px-4 py-2 bg-red-100 hover:bg-red-200 text-red-800 text-sm font-semibold rounded-md">
              Retry
            </button>
          </div>
        ) : isLoading ? (
          <VendorQueueSkeleton />
        ) : !vendors || vendors.length === 0 ? (
          <EmptyState 
            title="All Caught Up!" 
            description="There are no pending vendors awaiting approval at this time." 
          />
        ) : (
          <PendingVendorsTable 
            vendors={vendors} 
            isLoading={isLoading}
            onBulkApprove={handleBulkApprove}
            onBulkReject={handleBulkReject}
          />
        )}
      </div>
    </RoleGuard>
  );
}