"use client";

import { RoleGuard } from "@/components/auth/role-guard";
import { VendorForm } from "@/components/vendors/vendor-form";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function NewVendorPage() {
  return (
    <RoleGuard allow={["MAKER"]}>
      <div className="space-y-6 max-w-2xl">
        <div>
          <Link href="/maker" className="inline-flex items-center text-sm font-medium text-blue-600 hover:text-blue-800 mb-4 transition-colors">
            <ArrowLeft size={16} className="mr-1" /> Back to Dashboard
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Register New Vendor</h1>
          <p className="text-sm text-gray-500 mt-1">Submit bank details for compliance and checker review.</p>
        </div>
        
        <VendorForm />
      </div>
    </RoleGuard>
  );
}