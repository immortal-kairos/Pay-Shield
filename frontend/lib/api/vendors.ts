import { apiClient } from '@/lib/api/client';
import { CreateVendorPayload, RejectVendorPayload, Vendor } from '@/types/api';

export async function getVendors(params?: { status?: string }): Promise<Vendor[]> {
  const response = await apiClient.get<Vendor[]>('/api/vendors', { params });
  return response.data;
}

export async function getPendingVendors(): Promise<Vendor[]> {
  const response = await apiClient.get<Vendor[]>('/api/vendors', {
    params: { status: 'PENDING_REVIEW' },
  });
  return response.data;
}

export async function getActiveVendors(): Promise<Vendor[]> {
  const response = await apiClient.get<Vendor[]>('/api/vendors', {
    params: { status: 'ACTIVE' },
  });
  return response.data;
}

export async function createVendor(data: CreateVendorPayload): Promise<Vendor> {
  const response = await apiClient.post<Vendor>('/api/vendors', data);
  return response.data;
}

export async function approveVendor(vendorId: string): Promise<Vendor> {
  const response = await apiClient.post<Vendor>(`/api/vendors/${vendorId}/approve`);
  return response.data;
}

export async function rejectVendor(
  vendorId: string,
  payload?: RejectVendorPayload | { reason?: string }
): Promise<Vendor> {
  const response = await apiClient.post<Vendor>(`/api/vendors/${vendorId}/reject`, payload);
  return response.data;
}

// --- NEW BULK ACTION FUNCTIONS ---

export async function bulkApproveVendors(vendorIds: string[]) {
  const response = await apiClient.post('/api/vendors/bulk-approve', {
    vendor_ids: vendorIds,
  });
  return response.data;
}

export async function bulkRejectVendors(vendorIds: string[], reason: string) {
  const response = await apiClient.post('/api/vendors/bulk-reject', {
    vendor_ids: vendorIds,
    rejection_reason: reason,
  });
  return response.data;
}

export const vendorsApi = {
  getVendors,
  getPendingVendors,
  getActiveVendors,
  createVendor,
  approveVendor,
  rejectVendor,
  bulkApproveVendors, // Added to export
  bulkRejectVendors,  // Added to export
};

export default vendorsApi;