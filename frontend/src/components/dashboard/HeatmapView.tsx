"use client";

import { motion } from "framer-motion";

export default function HeatmapView() {
  return (
    <div className="w-full h-full min-h-[400px] flex items-center justify-center bg-surface p-4 relative">
      <div className="absolute top-4 left-4">
        <h3 className="font-semibold text-lg">National Issue Heatmap</h3>
        <p className="text-sm text-muted-foreground">Complaint volume by region</p>
      </div>
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="w-[80%] h-[70%] border-2 border-dashed border-border rounded-xl flex items-center justify-center text-muted-foreground bg-surface-raised"
      >
        ECharts Map Visualization Placeholder
      </motion.div>
    </div>
  );
}
