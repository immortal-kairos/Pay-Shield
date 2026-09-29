"use client";

import { Spinner } from "@/components/ui/spinner";
import { vendorsApi } from "@/lib/api/vendors";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle, XCircle } from "lucide-react";
import { useState } from "react";

export function VendorApprovalActions({ vendorId }: { vendorId: string }) {
  const queryClient = useQueryClient();
  const [isRejecting, setIsRejecting] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  const approveMutation = useMutation({
    mutationFn: () => vendorsApi.approveVendor(vendorId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["pending-vendors"] }),
    onError: () => setError("Approval failed. Try again."),
  });

  const rejectMutation = useMutation({
    mutationFn: () => vendorsApi.rejectVendor(vendorId, { reason: rejectReason }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["pending-vendors"] }),
    onError: () => setError("Rejection failed. Try again."),
  });

  const isPending = approveMutation.isPending || rejectMutation.isPending;

  if (isRejecting) {
    return (
      <div className="flex flex-col gap-2 min-w-[250px]">
        <input
          type="text"
          placeholder="Reason for rejection..."
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
          disabled={isPending}
          className="text-sm border rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-red-500"
          autoFocus
        />
        <div className="flex gap-2">
          <button
            onClick={() => rejectMutation.mutate()}
            disabled={!rejectReason.trim() || isPending}
            className="flex-1 text-xs bg-red-600 hover:bg-red-700 text-white py-1.5 rounded disabled:bg-gray-300 font-medium flex justify-center items-center"
          >
            {rejectMutation.isPending ? <Spinner className="w-4 h-4" /> : "Confirm"}
          </button>
          <button
            onClick={() => setIsRejecting(false)}
            disabled={isPending}
            className="flex-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 py-1.5 rounded font-medium"
          >
            Cancel
          </button>
        </div>
        {error && <span className="text-xs text-red-600">{error}</span>}
      </div>
    );
  }

  return (
    <div className="flex flex-col items-end gap-2">
      <div className="flex items-center gap-3">
        <button
          onClick={() => setIsRejecting(true)}
          disabled={isPending}
          className="flex items-center gap-1.5 text-sm font-medium text-red-600 hover:text-red-800 disabled:opacity-50 transition-colors"
        >
          <XCircle size={18} /> Reject
        </button>
        <div className="w-px h-4 bg-gray-200"></div>
        <button
          onClick={() => approveMutation.mutate()}
          disabled={isPending}
          className="flex items-center gap-1.5 text-sm font-medium text-emerald-600 hover:text-emerald-800 disabled:opacity-50 transition-colors"
        >
          {approveMutation.isPending ? <Spinner className="w-4 h-4" /> : <CheckCircle size={18} />} 
          Approve
        </button>
      </div>
      {error && <span className="text-xs text-red-600">{error}</span>}
    </div>
  );
}