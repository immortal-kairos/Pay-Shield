import { z } from "zod";

export const paymentFormSchema = z.object({
  vendor_id: z.string().uuid("Please select a valid vendor"),
  amount: z.coerce
    .number({ required_error: "Amount is required", invalid_type_error: "Amount must be a number" })
    .positive("Amount must be greater than zero")
    .multipleOf(0.01, "Amount cannot have more than 2 decimal places"),
  currency: z.string().length(3, "Currency must be a 3-letter code").default("INR"),
  execution_date: z.string().refine((val) => {
    const dateParts = val.split('-');
    if (dateParts.length !== 3) return false;
    
    const inputDate = new Date(parseInt(dateParts[0]), parseInt(dateParts[1]) - 1, parseInt(dateParts[2]));
    const today = new Date();
    today.setHours(0, 0, 0, 0); // Clear hour bounds to verify local browser date safely
    
    return inputDate >= today;
  }, { message: "Execution date must be today or in the future" }),
  notes: z.string().max(200, "Notes cannot exceed 200 characters").optional(),
});

export type PaymentFormValues = z.infer<typeof paymentFormSchema>;