const WEEKDAYS = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
];

export function formatCurrency(amount: number, currency: string = 'INR'): string {
  try {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: currency || 'INR',
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `${currency} ${amount.toLocaleString('en-IN')}`;
  }
}

export function formatCurrencyINR(amount: number): string {
  return formatCurrency(amount, 'INR');
}

export function formatCompactNumber(value: number): string {
  if (value >= 10000000) {
    return `₹${(value / 10000000).toFixed(1)} Cr`;
  }
  if (value >= 100000) {
    return `₹${(value / 100000).toFixed(1)} L`;
  }
  if (value >= 1000) {
    return `₹${(value / 1000).toFixed(1)} k`;
  }
  return `₹${value.toLocaleString('en-IN')}`;
}

export function formatDate(dateString: string): string {
  if (!dateString) return '-';
  try {
    const d = new Date(dateString);
    return d.toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return dateString;
  }
}

export function formatFeatureLabel(key: string): string {
  const labelMap: Record<string, string> = {
    amount: 'Transaction Amount',
    currency_code_encoded: 'Currency Code Mapping',
    execution_day_of_week: 'Execution Day of Week',
    execution_day_of_month: 'Execution Day of Month',
    lead_time_days: 'Transfer Lead Time',
    vendor_age_days: 'Vendor Relationship Age',
    maker_payment_count_30d: 'Maker 30-Day Volume',
    vendor_payment_count_30d: 'Vendor 30-Day Volume',
    maker_avg_amount_30d: 'Maker 30-Day Average',
    vendor_avg_amount_30d: 'Vendor 30-Day Average',
    amount_vs_maker_avg_ratio: 'Amount vs Maker Historical Ratio',
    amount_vs_vendor_avg_ratio: 'Amount vs Vendor Historical Ratio',
    recent_org_payment_count_24h: 'Org 24h Transaction Velocity',
    is_new_vendor_flag: 'New Vendor Flag (< 30 Days)',
    is_high_amount_flag: 'High Amount Flag (≥ ₹10L)',
  };
  return labelMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function describeFeatureValue(
  key: string,
  value: number | string | null | undefined,
  currency: string = 'INR'
): { displayValue: string; highlight?: 'neutral' | 'warning' | 'danger' | 'info' } {
  if (value === null || value === undefined) {
    return { displayValue: 'Not Available', highlight: 'neutral' };
  }

  const num = typeof value === 'number' ? value : Number(value);

  switch (key) {
    case 'amount':
      return {
        displayValue: formatCurrency(num, currency),
        highlight: num >= 1000000 ? 'danger' : 'neutral',
      };
    case 'currency_code_encoded': {
      const currencies: Record<number, string> = { 1: 'INR (1)', 2: 'USD (2)', 3: 'EUR (3)' };
      return { displayValue: currencies[num] || `Other (${num})`, highlight: 'neutral' };
    }
    case 'execution_day_of_week': {
      const dayName = WEEKDAYS[num] ?? `Day ${num}`;
      const isWeekend = num === 5 || num === 6;
      return {
        displayValue: isWeekend ? `${dayName} (Weekend Processing)` : dayName,
        highlight: isWeekend ? 'warning' : 'neutral',
      };
    }
    case 'execution_day_of_month':
      return { displayValue: `Day ${num} of Month`, highlight: 'neutral' };
    case 'lead_time_days':
      return {
        displayValue: num === 0 ? '0 Days (Immediate / Same-Day)' : `${num} Day${num > 1 ? 's' : ''}`,
        highlight: num === 0 ? 'warning' : 'neutral',
      };
    case 'vendor_age_days':
      return {
        displayValue: `${Math.round(num)} Day${num === 1 ? '' : 's'} on Platform`,
        highlight: num < 30 ? 'warning' : 'neutral',
      };
    case 'maker_payment_count_30d':
      return { displayValue: `${num} payment${num === 1 ? '' : 's'} submitted`, highlight: 'neutral' };
    case 'vendor_payment_count_30d':
      return { displayValue: `${num} payment${num === 1 ? '' : 's'} received`, highlight: 'neutral' };
    case 'maker_avg_amount_30d':
    case 'vendor_avg_amount_30d':
      return { displayValue: formatCurrency(num, currency), highlight: 'neutral' };
    case 'amount_vs_maker_avg_ratio':
    case 'amount_vs_vendor_avg_ratio': {
      const formattedRatio = `${num.toFixed(2)}× Mean`;
      let highlight: 'neutral' | 'warning' | 'danger' = 'neutral';
      if (num >= 5.0) highlight = 'danger';
      else if (num >= 2.5) highlight = 'warning';
      return { displayValue: formattedRatio, highlight };
    }
    case 'recent_org_payment_count_24h':
      return {
        displayValue: `${num} transaction${num === 1 ? '' : 's'}`,
        highlight: num >= 10 ? 'warning' : 'neutral',
      };
    case 'is_new_vendor_flag':
      return {
        displayValue: num === 1 ? 'Active Flag (New Vendor Account)' : 'Inactive (Established Vendor)',
        highlight: num === 1 ? 'warning' : 'neutral',
      };
    case 'is_high_amount_flag':
      return {
        displayValue: num === 1 ? 'Active Flag (High Volume Value)' : 'Normal Transaction Tier',
        highlight: num === 1 ? 'danger' : 'neutral',
      };
    default:
      return { displayValue: String(value), highlight: 'neutral' };
  }
}