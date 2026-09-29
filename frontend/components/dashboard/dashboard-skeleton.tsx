export function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 w-64 bg-gray-200 rounded"></div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-xl border border-gray-100 p-6 h-32">
            <div className="h-4 w-24 bg-gray-100 rounded mb-4"></div>
            <div className="h-8 w-32 bg-gray-200 rounded"></div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-100 p-6 h-96"></div>
        <div className="bg-white rounded-xl border border-gray-100 p-6 h-96"></div>
      </div>
    </div>
  );
}