"use client";

import { formatCompactNumber } from "@/lib/utils/format";
import { TopVendor } from "@/types/api";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { EmptyState } from "./empty-state";

export function TopVendorsCard({ vendors }: { vendors: TopVendor[] }) {
    if (!vendors || vendors.length === 0) {
    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 h-full">
        <h3 className="text-base font-semibold text-gray-900 mb-4">Top Vendors</h3>
        <EmptyState title="No Vendor Data" description="Approved volume data will appear here once payments are processed." />
        </div>
    );
    }

    return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 h-full flex flex-col">
        <h3 className="text-base font-semibold text-gray-900 mb-6">Top Vendors by Volume</h3>
        <div className="flex-1 min-h-[250px]">
        <ResponsiveContainer width="100%" height="100%">
            <BarChart data={vendors} layout="vertical" margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
            <XAxis type="number" hide />
            <YAxis dataKey="vendor_name" type="category" axisLine={false} tickLine={false} width={100} tick={{ fontSize: 12, fill: '#4B5563' }} />
            <Tooltip
            formatter={(value: any) => [`₹${formatCompactNumber(Number(value))}`, 'Volume']}
            cursor={{ fill: '#F3F4F6' }}
            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
            <Bar dataKey="approved_volume" fill="#3B82F6" radius={[0, 4, 4, 0]} barSize={24} />
            </BarChart>
        </ResponsiveContainer>
        </div>
    </div>
    );
}
