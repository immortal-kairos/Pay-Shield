export function VendorQueueSkeleton() {
  return (
    <div className="space-y-4">
      {[...Array(3)].map((_, i) => (
        <div key={i} className="bg-white p-6 rounded-xl border border-gray-100 flex items-center justify-between animate-pulse">
          <div className="space-y-3">
            <div className="h-5 w-48 bg-gray-200 rounded"></div>
            <div className="h-4 w-32 bg-gray-100 rounded"></div>
          </div>
          <div className="flex gap-2">
            <div className="h-10 w-24 bg-gray-200 rounded"></div>
            <div className="h-10 w-24 bg-gray-200 rounded"></div>
          </div>
        </div>
      ))}
    </div>
  );
}