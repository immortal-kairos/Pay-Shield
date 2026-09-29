import { PlusCircle, Users } from "lucide-react";
import { RecentPaymentsTable } from "./recent-payments-table";
import { PaymentListItem } from "@/types/api";
import Link from "next/link";

interface MakerTaskPanelProps {
  payments: PaymentListItem[];
  isLoading: boolean;
  error: Error | null;
}

export function MakerTaskPanel({ payments, isLoading, error }: MakerTaskPanelProps) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        <Link href="/maker/payments/new" className="flex items-center justify-center gap-3 p-6 bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-sm transition-all font-semibold">
          <PlusCircle size={20} />
          Initiate New Payment
        </Link>
        
        <Link href="/maker/vendors/new" className="flex items-center justify-center gap-3 p-6 bg-white hover:bg-gray-50 text-blue-900 border border-gray-200 rounded-xl shadow-sm transition-all font-semibold">
          <Users size={20} />
          Register New Vendor
        </Link>

      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Your Recent Submissions</h3>
        <RecentPaymentsTable payments={payments} isLoading={isLoading} error={error} />
      </div>
    </div>
  );
}