"use client";

import { motion } from "framer-motion";

export default function HeatmapView() {
  return (
    <div className="relative flex min-h-[320px] w-full min-w-0 items-center justify-center bg-surface p-4 sm:min-h-[400px]">
      <div className="absolute left-4 right-4 top-4 min-w-0">
        <h3 className="break-words text-lg font-semibold">National Issue Heatmap</h3>
        <p className="text-sm text-muted-foreground">Complaint volume by region</p>
      </div>
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="flex h-[65%] w-full max-w-3xl items-center justify-center rounded-xl border-2 border-dashed border-border bg-surface-raised p-4 text-center text-muted-foreground sm:w-[80%] sm:p-0"
      >
        ECharts Map Visualization Placeholder
      </motion.div>
    </div>
  );
}
