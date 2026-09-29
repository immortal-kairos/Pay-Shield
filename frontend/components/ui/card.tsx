import { cn } from "@/lib/utils/cn";
import * as React from "react";

export const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("rounded-lg border bg-white text-gray-950 shadow-sm", className)} {...props} />
  )
);
Card.displayName = "Card";