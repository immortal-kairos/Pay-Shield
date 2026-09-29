import { apiClient } from '@/lib/api/client';
import {
  CreatePaymentPayload,
  Payment,
  PaymentListItem,
  RejectPaymentPayload,
  Vendor,
} from '@/types/api';

// 1. Add getApprovedVendors function
export async function getApprovedVendors(): Promise<Vendor[]> {
  const response = await apiClient.get<Vendor[]>('/api/vendors', {
    params: { status: 'ACTIVE' },
  });
  return response.data;
}

export async function getPendingPayments(): Promise<Payment[]> {
  const response = await apiClient.get<Payment[]>('/api/payments', {
    params: { status: 'PENDING_APPROVAL' },
  });
  return response.data;
}

export async function getRecentPayments(
  limitOrOptions: number | { limit?: number } = 5
): Promise<PaymentListItem[]> {
  const limit =
    typeof limitOrOptions === 'number'
      ? limitOrOptions
      : (limitOrOptions?.limit ?? 5);

  const response = await apiClient.get<PaymentListItem[]>('/api/payments', {
    params: { limit },
  });
  return response.data;
}

export async function createPayment(payload: CreatePaymentPayload): Promise<Payment> {
  const response = await apiClient.post<Payment>('/api/payments', payload);
  return response.data;
}

export async function approvePayment(paymentId: string): Promise<Payment> {
  const response = await apiClient.post<Payment>(`/api/payments/${paymentId}/approve`);
  return response.data;
}

export async function rejectPayment(
  paymentId: string,
  payload: RejectPaymentPayload
): Promise<Payment> {
  const response = await apiClient.post<Payment>(`/api/payments/${paymentId}/reject`, payload);
  return response.data;
}

// --- NEW BULK ACTION FUNCTIONS ---

export async function bulkApprovePayments(paymentIds: string[]) {
  const response = await apiClient.post('/api/payments/bulk-approve', {
    payment_ids: paymentIds,
  });
  return response.data;
}

export async function bulkRejectPayments(paymentIds: string[], reason: string) {
  const response = await apiClient.post('/api/payments/bulk-reject', {
    payment_ids: paymentIds,
    rejection_reason: reason,
  });
  return response.data;
}

// 2. Export everything in the paymentsApi object
export const paymentsApi = {
  getApprovedVendors,
  getPendingPayments,
  getRecentPayments,
  createPayment,
  approvePayment,
  rejectPayment,
  bulkApprovePayments, // Added here
  bulkRejectPayments,  // Added here
};

export default paymentsApi;