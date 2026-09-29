import { z } from "zod";

export const vendorFormSchema = z.object({
  name: z.string().min(2, "Company name must be at least 2 characters"),
  tax_id: z.string()
    .min(9, "Tax ID must be at least 9 characters")
    .regex(/^[a-zA-Z0-9]+$/, "Tax ID must be alphanumeric"),
  bank_name: z.string().min(2, "Bank name must be at least 2 characters"),
  account_number: z.string()
    .min(8, "Account number must be at least 8 digits")
    .max(18, "Account number cannot exceed 18 digits")
    .regex(/^\d+$/, "Account number must contain only numbers"),
  routing_number: z.string()
    .min(4, "Routing number must be at least 4 characters")
    .regex(/^[a-zA-Z0-9]+$/, "Routing number must be alphanumeric"),
  contact_email: z.string().email("Please enter a valid email address"),
});

export type VendorFormValues = z.infer<typeof vendorFormSchema>;