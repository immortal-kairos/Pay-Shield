"use client";

import { Spinner } from "@/components/ui/spinner";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertCircle } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { SubmitHandler, useForm } from "react-hook-form";
import { paymentsApi } from "../../lib/api/payments";
import { paymentFormSchema, PaymentFormValues } from "../../lib/validation/payment";

export function PaymentForm() {
  const router = useRouter();
  const [apiError, setApiError] = useState<string | null>(null);

  const { data: vendors, isLoading: vendorsLoading, error: vendorsError } = useQuery({
    queryKey: ["approved-vendors"],
    queryFn: paymentsApi.getApprovedVendors,
  });

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty, isValid },
  } = useForm<PaymentFormValues>({
    resolver: zodResolver(paymentFormSchema) as any,
    mode: "onChange",
    defaultValues: {
      vendor_id: "",
      amount: 0,
      currency: "INR",
      execution_date: "",
      notes: "",
    },
  });

  const mutation = useMutation({
    mutationFn: paymentsApi.createPayment,
    onSuccess: () => {
      router.push("/maker?success=payment_created");
    },
    onError: (error: any) => {
      setApiError(error.response?.data?.detail || "Failed to initiate payment. Please try again.");
    },
  });

  const onSubmit: SubmitHandler<PaymentFormValues> = (data) => {
    setApiError(null);
    mutation.mutate(data);
  };

  const isPending = mutation.isPending;
  const hasNoVendors = !vendorsLoading && (!vendors || vendors.length === 0);

  if (vendorsError) {
    return (
      <div className="p-4 bg-red-50 text-red-700 rounded-lg border border-red-200 text-sm font-medium">
        Failed to load approved vendors. Please refresh the page.
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 max-w-2xl space-y-6">
      {hasNoVendors && (
        <div className="p-4 bg-amber-50 rounded-lg border border-amber-200 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-amber-800 font-semibold">
            <AlertCircle size={18} />
            No Approved Vendors Available
          </div>
          <p className="text-sm text-amber-700">
            You must register and receive approval for at least one vendor before initiating a payment.
          </p>
          <Link href="/maker/vendors/new" className="text-sm font-semibold text-blue-600 hover:text-blue-800 underline mt-1">
            Register a New Vendor &rarr;
          </Link>
        </div>
      )}

      {apiError && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg border border-red-200 text-sm font-medium">
          {apiError}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2 md:col-span-2">
          <label className="text-sm font-semibold text-gray-700">Select Vendor</label>
          <select
            {...register("vendor_id")}
            disabled={isPending || hasNoVendors || vendorsLoading}
            className={`w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none bg-white ${errors.vendor_id ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
          >
            <option value="">{vendorsLoading ? "Loading vendors..." : "Select an approved vendor"}</option>
            {vendors?.map(v => (
              <option key={v.id} value={v.id}>{v.name}</option>
            ))}
          </select>
          {errors.vendor_id && <p className="text-xs text-red-600">{errors.vendor_id.message}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-gray-700">Amount</label>
          <input
            type="number"
            step="0.01"
            {...register("amount")}
            disabled={isPending || hasNoVendors}
            className={`w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none ${errors.amount ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
            placeholder="0.00"
          />
          {errors.amount && <p className="text-xs text-red-600">{errors.amount.message}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-gray-700">Currency</label>
          <select
            {...register("currency")}
            disabled={isPending || hasNoVendors}
            className={`w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none bg-white ${errors.currency ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
          >
            <option value="INR">INR - Indian Rupee</option>
            <option value="USD">USD - US Dollar</option>
            <option value="EUR">EUR - Euro</option>
          </select>
          {errors.currency && <p className="text-xs text-red-600">{errors.currency.message}</p>}
        </div>

        <div className="space-y-2 md:col-span-2">
          <label className="text-sm font-semibold text-gray-700">Execution Date</label>
          <input
            type="date"
            {...register("execution_date")}
            disabled={isPending || hasNoVendors}
            className={`w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none ${errors.execution_date ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
          />
          {errors.execution_date && <p className="text-xs text-red-600">{errors.execution_date.message}</p>}
        </div>

        <div className="space-y-2 md:col-span-2">
          <label className="text-sm font-semibold text-gray-700">Notes / Reference (Optional)</label>
          <textarea
            {...register("notes")}
            disabled={isPending || hasNoVendors}
            rows={3}
            className={`w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none ${errors.notes ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
            placeholder="Invoice #12345, Q2 Supplier Payment..."
          />
          {errors.notes && <p className="text-xs text-red-600">{errors.notes.message}</p>}
        </div>
      </div>

      <div className="pt-4 flex justify-end">
        <button
          type="submit"
          disabled={!isDirty || !isValid || isPending || hasNoVendors}
          className="flex items-center justify-center min-w-[140px] px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
        >
          {isPending ? <Spinner className="w-5 h-5" /> : "Submit for Approval"}
        </button>
      </div>
    </form>
  );
}