"use client";

import { motion } from "framer-motion";
import StatsCard from "@/components/dashboard/StatsCard";
import HeatmapView from "@/components/dashboard/HeatmapView";
import ComplaintFeed from "@/components/dashboard/ComplaintFeed";

export default function DashboardHome() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Overview</h1>
          <p className="text-muted-foreground">
            Monitor MBG operational intelligence and signals.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard title="Total Complaints" value="1,245" trend="+12%" />
        <StatsCard title="Reports Verified" value="8,432" trend="+5%" />
        <StatsCard title="Average Severity" value="High" trend="Stable" />
        <StatsCard title="Flagged Anomalies" value="14" trend="-2" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="col-span-1 lg:col-span-2 bg-surface-raised border rounded-xl overflow-hidden shadow-sm">
          <HeatmapView />
        </div>
        <div className="bg-surface-raised border rounded-xl shadow-sm flex flex-col h-[500px]">
          <div className="p-4 border-b">
            <h2 className="font-semibold text-lg">Live Signals Feed</h2>
          </div>
          <div className="flex-1 overflow-y-auto">
            <ComplaintFeed />
          </div>
        </div>
      </div>
    </div>
  );
}
