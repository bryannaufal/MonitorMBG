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
      className="min-w-0 rounded-xl border bg-surface-raised p-4 shadow-sm sm:p-5"
    >
      <h3 className="mb-2 break-words text-sm font-medium text-muted-foreground">{title}</h3>
      <div className="flex flex-wrap items-end justify-between gap-2">
        <span className="break-words text-2xl font-bold sm:text-3xl">{value}</span>
        <span
          className={`break-words text-sm font-medium ${
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
