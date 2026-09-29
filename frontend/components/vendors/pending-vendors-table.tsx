"use client";

import { BulkActionToolbar } from "@/components/shared/bulk-action-toolbar";
import { BulkRejectModal } from "@/components/shared/bulk-reject-modal";
import { useKeyboardShortcuts } from "@/hooks/use-keyboard-shortcuts";
import { useRowSelection } from "@/hooks/use-row-selection";
import { formatDate } from "@/lib/utils/format";
import { Vendor } from "@/types/api";
import { Building2, CheckCircle2, Landmark, Mail } from "lucide-react";
import { useState } from "react";
import { VendorApprovalActions } from "./vendor-approval-actions";

interface PendingVendorsTableProps {
  vendors: Vendor[];
  isLoading?: boolean;
  onBulkApprove: (vendorIds: string[]) => Promise<void>;
  onBulkReject: (vendorIds: string[], reason: string) => Promise<void>;
}

export function PendingVendorsTable({
  vendors,
  isLoading,
  onBulkApprove,
  onBulkReject,
}: PendingVendorsTableProps) {
  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  // --- 1. The Strict Selection Hook ---
  const availableIds = vendors.map((v) => v.id);
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
      disabled: selectedIds.size === 0,
      handler: clear
    },
    {
      key: 'a',
      altKey: true,
      preventDefault: true,
      disabled: vendors.length === 0,
      handler: toggleAll
    }
  ]);

  // --- 2. Execution Wrappers (No High-Risk check needed for Vendors) ---
  const executeBulkApprove = async () => {
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

  if (isLoading) {
    return (
      <div className="w-full bg-white rounded-xl border border-slate-200 p-12 text-center">
        <div className="inline-block animate-spin w-8 h-8 border-4 border-slate-300 border-t-indigo-600 rounded-full mb-3" />
        <p className="text-sm font-medium text-slate-500">Loading pending vendors...</p>
      </div>
    );
  }

  if (vendors.length === 0) {
    return (
      <div className="w-full bg-white rounded-xl border border-slate-200 p-12 text-center">
        <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-3">
          <CheckCircle2 className="w-6 h-6" />
        </div>
        <h3 className="text-base font-bold text-slate-800">No Vendors Pending</h3>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          There are currently no new vendor accounts awaiting checker sign-off.
        </p>
      </div>
    );
  }

  return (
    <div className="relative pb-16">
      {/* Select All Header */}
      <div className="mb-4 flex items-center gap-3 px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg">
        <input
          type="checkbox"
          id="selectAllVendors"
          className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-600 w-4 h-4 cursor-pointer"
          checked={isAllSelected}
          onChange={toggleAll}
        />
        <label htmlFor="selectAllVendors" className="text-sm font-medium text-slate-700 cursor-pointer select-none">
          Select All Pending Vendors
        </label>
      </div>

      <div className="space-y-4">
        {vendors.map((vendor) => {
          const isRowSelected = isSelected(vendor.id);
          
          return (
            <div 
              key={vendor.id} 
              className={`rounded-xl shadow-sm border p-6 flex flex-col lg:flex-row lg:items-center justify-between gap-6 transition-all hover:shadow-md ${
                isRowSelected ? 'bg-indigo-50/60 border-indigo-200' : 'bg-white border-gray-100'
              }`}
            >
              <div className="flex items-start lg:items-center gap-4 flex-1">
                {/* Checkbox */}
                <div className="pt-1 lg:pt-0">
                  <input
                    type="checkbox"
                    className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-600 w-4 h-4 cursor-pointer"
                    checked={isRowSelected}
                    onChange={() => toggle(vendor.id)}
                  />
                </div>
                
                {/* Original Card Content */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4 flex-1">
                  
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Building2 size={16} className="text-gray-400" />
                      <h3 className="font-bold text-gray-900">{vendor.name}</h3>
                    </div>
                    <p className="text-xs text-gray-500 pl-6">Tax ID: <span className="font-medium text-gray-900">{vendor.tax_id}</span></p>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Landmark size={16} className="text-gray-400" />
                      <span className="text-sm font-medium text-gray-900">{vendor.bank_name}</span>
                    </div>
                    <p className="text-xs text-gray-500 pl-6">
                      Acct: <span className="font-medium text-gray-900">{vendor.account_number_masked || '****'}</span> • 
                      Routing: <span className="font-medium text-gray-900">{vendor.routing_number}</span>
                    </p>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Mail size={16} className="text-gray-400" />
                      <span className="text-sm text-gray-600">{vendor.contact_email}</span>
                    </div>
                  </div>

                  <div className="flex items-center">
                    <span className="text-xs text-gray-400">
                      Submitted: {vendor.created_at ? formatDate(vendor.created_at) : 'Recently'}
                    </span>
                  </div>

                </div>
              </div>

              {/* Preserved Single-Item Action Component */}
              <div className="pt-4 lg:pt-0 border-t lg:border-t-0 lg:border-l border-gray-100 lg:pl-6 flex items-center lg:justify-end">
                <VendorApprovalActions vendorId={vendor.id} />
              </div>
            </div>
          );
        })}
      </div>

      <BulkActionToolbar
        selectedCount={selectedIds.size}
        onApprove={executeBulkApprove}
        onReject={() => setIsRejectModalOpen(true)}
        onClear={clear}
        isProcessing={isProcessing}
      />

      <BulkRejectModal
        isOpen={isRejectModalOpen}
        selectedCount={selectedIds.size}
        onSubmit={executeBulkReject}
        onCancel={() => setIsRejectModalOpen(false)}
      />
    </div>
  );
}