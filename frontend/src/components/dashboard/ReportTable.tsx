"use client";

import { Search, Filter } from "lucide-react";

export default function ReportTable() {
  return (
    <div className="w-full bg-surface border rounded-xl overflow-hidden">
      <div className="p-4 border-b border-border flex justify-between items-center bg-surface-raised">
        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search reports..."
            className="pl-9 pr-4 py-2 bg-surface border rounded-md text-sm w-64 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>
        <button className="flex items-center gap-2 px-3 py-2 border rounded-md text-sm hover:bg-surface-raised transition-colors">
          <Filter className="h-4 w-4" /> Filter
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-muted-foreground uppercase bg-surface-overlay border-b">
            <tr>
              <th className="px-6 py-3 font-medium">Report ID</th>
              <th className="px-6 py-3 font-medium">Region</th>
              <th className="px-6 py-3 font-medium">Status</th>
              <th className="px-6 py-3 font-medium">Date</th>
              <th className="px-6 py-3 font-medium text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-border hover:bg-surface-raised/50 transition-colors">
              <td className="px-6 py-4 font-mono">#REP-1029</td>
              <td className="px-6 py-4">Jakarta Selatan</td>
              <td className="px-6 py-4">
                <span className="px-2 py-1 text-xs rounded-full bg-severity-low/10 text-severity-low border border-severity-low/20">Verified</span>
              </td>
              <td className="px-6 py-4 text-muted-foreground">Oct 24, 2026</td>
              <td className="px-6 py-4 text-right">
                <button className="text-brand-500 hover:underline">View</button>
              </td>
            </tr>
            {/* Add more placeholder rows as needed */}
          </tbody>
        </table>
      </div>
    </div>
  );
}
