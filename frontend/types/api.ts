export type UserRole = 'MAKER' | 'CHECKER' | 'ADMIN' | 'AUDITOR_READONLY';

export type VendorStatus = 'PENDING_REVIEW' | 'ACTIVE' | 'REJECTED';

export type PaymentStatus =
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'REJECTED'
  | 'CANCELLED'
  | 'TRANSFER_INITIATED'
  | 'TRANSFER_SUCCESS'
  | 'TRANSFER_FAILED';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

// Vendor Types (Supports both Indian IFSC & US/Generic Routing/Bank schemas)
export interface Vendor {
  id: string;
  org_id: string;
  name: string;
  contact_email: string;
  bank_name?: string;
  account_number_masked?: string;
  bank_account_last4?: string;
  bank_account_hash?: string;
  bank_account_encrypted?: string | null;
  routing_number?: string;
  ifsc_code?: string;
  tax_id?: string | null;
  status: VendorStatus;
  created_by_user_id: string;
  approved_by_user_id?: string | null;
  rejection_reason?: string | null;
  created_at: string;
  updated_at?: string;
  bank_account_updated_at?: string;
}

export interface CreateVendorPayload {
  name: string;
  contact_email: string;
  bank_account_number?: string; // Optional for backward compatibility
  account_number?: string;      // US layout
  ifsc_code?: string;           // Indian layout
  routing_number?: string;      // US layout
  bank_name?: string;           // Optional extra
  tax_id?: string;              // Optional extra
}

export interface RejectVendorPayload {
  rejection_reason?: string;
  reason?: string;
}

// Payment Types
export interface MlFeatureSnapshot {
  amount: number;
  currency_code_encoded: number;
  execution_day_of_week: number;
  execution_day_of_month: number;
  lead_time_days: number;
  vendor_age_days: number;
  maker_payment_count_30d: number;
  vendor_payment_count_30d: number;
  maker_avg_amount_30d: number;
  vendor_avg_amount_30d: number;
  amount_vs_maker_avg_ratio: number;
  amount_vs_vendor_avg_ratio: number;
  recent_org_payment_count_24h: number;
  is_new_vendor_flag: number;
  is_high_amount_flag: number;
}

export interface Payment {
  id: string;
  org_id: string;
  vendor_id: string;
  vendor_name?: string | null;
  amount: number;
  currency: string;
  payment_date: string;
  execution_date?: string;
  reference_note?: string | null;
  notes?: string | null;
  status: PaymentStatus;
  risk_score: number;
  risk_level: RiskLevel;
  risk_flags?: string[];
  created_by_user_id: string;
  reviewed_by_user_id?: string | null;
  rejection_reason?: string | null;
  created_at: string;
  updated_at?: string;

  // ML Risk Scoring Fields
  ml_risk_score: number | null;
  ml_risk_label: RiskLevel | string | null;
  ml_feature_snapshot: MlFeatureSnapshot | Record<string, number | string | null> | null;
  ml_available: boolean;
}

export type PaymentListItem = Payment;

export interface CreatePaymentPayload {
  vendor_id: string;
  amount: number;
  currency: string;
  execution_date?: string;
  payment_date?: string;
  notes?: string;
  reference_note?: string;
}

export interface RejectPaymentPayload {
  rejection_reason?: string;
  reason?: string;
}

// Analytics & Dashboard Metrics (Supports all metric aliases)
export interface TopVendor {
  id: string;
  name: string;
  total_amount: number;
  payment_count: number;
  currency?: string;
}

export interface DashboardMetrics {
  total_volume?: number;
  total_volume_30d?: number;
  total_volume_currency?: string;
  pending_count?: number;
  pending_payments_count?: number;
  pending_payments_volume?: number;
  high_risk_count?: number;
  approved_count?: number;
  active_vendors_count?: number;
  flagged_anomalies_count?: number;
  recent_payments?: Payment[];
  top_vendors?: TopVendor[];
}