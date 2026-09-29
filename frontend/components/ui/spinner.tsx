import { cn } from "@/lib/utils/cn";
import { Loader2 } from "lucide-react";

export const Spinner = ({ className }: { className?: string }) => {
  return <Loader2 className={cn("h-4 w-4 animate-spin", className)} />;
};