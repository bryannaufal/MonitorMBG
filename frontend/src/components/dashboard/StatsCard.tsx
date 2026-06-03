"use client";

import { motion } from "framer-motion";

interface StatsCardProps {
  title: string;
  value: string;
  trend: string;
}

export default function StatsCard({ title, value, trend }: StatsCardProps) {
  const isPositive = trend.startsWith("+");
  const isNegative = trend.startsWith("-");
  const isStable = trend === "Stable";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-surface-raised border rounded-xl p-5 shadow-sm"
    >
      <h3 className="text-sm font-medium text-muted-foreground mb-2">{title}</h3>
      <div className="flex items-end justify-between">
        <span className="text-3xl font-bold">{value}</span>
        <span
          className={`text-sm font-medium ${
            isPositive
              ? "text-severity-low"
              : isNegative
              ? "text-severity-high"
              : "text-muted-foreground"
          }`}
        >
          {trend}
        </span>
      </div>
    </motion.div>
  );
}
