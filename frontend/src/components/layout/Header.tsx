"use client";

import { Bell, Search, User } from "lucide-react";
import MobileNav from "./MobileNav";

export default function Header() {
  return (
    <header className="h-16 px-6 bg-surface border-b border-border flex items-center justify-between shrink-0">
      <div className="flex items-center gap-4">
        <MobileNav />
        <div className="hidden md:flex items-center relative">
          <Search className="h-4 w-4 absolute left-3 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search reports, complaints..."
            className="h-9 w-64 md:w-80 rounded-md border border-border bg-surface-raised pl-9 pr-4 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500 transition-shadow"
          />
        </div>
      </div>
      <div className="flex items-center gap-4">
        <button className="relative p-2 rounded-full hover:bg-surface-raised transition-colors">
          <Bell className="h-5 w-5 text-muted-foreground" />
          <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-destructive" />
        </button>
        <button className="h-8 w-8 rounded-full bg-brand-500/20 text-brand-500 flex items-center justify-center border border-brand-500/30">
          <User className="h-4 w-4" />
        </button>
      </div>
    </header>
  );
}
