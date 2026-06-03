"use client";

import { motion, AnimatePresence } from "framer-motion";
import TicketCard from "./TicketCard";

const DUMMY_FEED = [
  { id: 1, source: "Twitter", severity: "high", title: "Missing portions in Jakarta Selatan", time: "2 min ago" },
  { id: 2, source: "Instagram", severity: "medium", title: "Quality concern: cold food", time: "15 min ago" },
  { id: 3, source: "WhatsApp", severity: "low", title: "Delivery delayed by 30 mins", time: "1 hour ago" },
];

export default function ComplaintFeed() {
  return (
    <div className="p-4 space-y-3">
      <AnimatePresence>
        {DUMMY_FEED.map((item, index) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ delay: index * 0.1 }}
          >
            <TicketCard {...item} />
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
