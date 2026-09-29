"use client";

import { Spinner } from "@/components/ui/spinner";
import { vendorsApi } from "@/lib/api/vendors";
import { vendorFormSchema, VendorFormValues } from "@/lib/validation/vendor";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

export function VendorForm() {
  const router = useRouter();
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty, isValid },
  } = useForm<VendorFormValues>({
    resolver: zodResolver(vendorFormSchema),
    mode: "onChange",
  });

  const mutation = useMutation({
    mutationFn: vendorsApi.createVendor,
    onSuccess: () => {
      router.push("/maker?success=vendor_created");
    },
    onError: (error: any) => {
      setApiError(error.response?.data?.detail || "Failed to register vendor. Please try again.");
    },
  });

  const onSubmit = (data: VendorFormValues) => {
    setApiError(null);
    mutation.mutate(data);
  };

  const isPending = mutation.isPending;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 max-w-2xl space-y-6">
      {apiError && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg border border-red-200 text-sm font-medium">
          {apiError}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <label className="text-sm font-semibold text-gray-700">Company Name</label>
          <input
            {...register("name")}
            disabled={isPending}
            className={`w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none ${errors.name ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
            placeholder="Acme Corp"
          />
          {errors.name && <p className="text-xs text-red-600">{errors.name.message}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-gray-700">Tax ID / EIN</label>
          <input
            {...register("tax_id")}
            disabled={isPending}
            className={`w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none ${errors.tax_id ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
            placeholder="ABCD12345"
          />
          {errors.tax_id && <p className="text-xs text-red-600">{errors.tax_id.message}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-gray-700">Bank Name</label>
          <input
            {...register("bank_name")}
            disabled={isPending}
            className={`w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none ${errors.bank_name ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
            placeholder="HDFC Bank"
          />
          {errors.bank_name && <p className="text-xs text-red-600">{errors.bank_name.message}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-gray-700">Contact Email</label>
          <input
            {...register("contact_email")}
            type="email"
            disabled={isPending}
            className={`w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none ${errors.contact_email ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
            placeholder="finance@acme.com"
          />
          {errors.contact_email && <p className="text-xs text-red-600">{errors.contact_email.message}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-gray-700">Account Number</label>
          <input
            {...register("account_number")}
            disabled={isPending}
            className={`w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none ${errors.account_number ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
            placeholder="1234567890"
          />
          {errors.account_number && <p className="text-xs text-red-600">{errors.account_number.message}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-gray-700">Routing Number / IFSC</label>
          <input
            {...register("routing_number")}
            disabled={isPending}
            className={`w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none ${errors.routing_number ? 'border-red-500 bg-red-50' : 'border-gray-300'}`}
            placeholder="HDFC0001234"
          />
          {errors.routing_number && <p className="text-xs text-red-600">{errors.routing_number.message}</p>}
        </div>
      </div>

      <div className="pt-4 flex justify-end">
        <button
          type="submit"
          disabled={!isDirty || !isValid || isPending}
          className="flex items-center justify-center min-w-[140px] px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
        >
          {isPending ? <Spinner className="w-5 h-5" /> : "Submit for Approval"}
        </button>
      </div>
    </form>
  );
}