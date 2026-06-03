"use client";

import { Menu } from "lucide-react";

export default function MobileNav() {
  return (
    <div className="md:hidden">
      <button className="p-2 -ml-2 rounded-md hover:bg-surface-raised transition-colors">
        <Menu className="h-5 w-5" />
      </button>
    </div>
  );
}
