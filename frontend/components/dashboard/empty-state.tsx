import { FileSearch } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description: string;
}

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center bg-gray-50 border border-dashed border-gray-200 rounded-lg">
      <FileSearch className="h-10 w-10 text-gray-400 mb-4" />
      <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
      <p className="text-sm text-gray-500 mt-1 max-w-sm">{description}</p>
    </div>
  );
}