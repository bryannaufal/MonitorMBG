"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  Activity,
  Bot,
  ClipboardList,
  Factory,
  FileSearch,
  GitBranch,
  History,
  Inbox,
  LayoutDashboard,
  Map,
  Menu,
  ShieldAlert,
  X,
} from "lucide-react";

import { cn } from "@/lib/utils";

const mobileItems = [
  { name: "Command Center", href: "/", icon: LayoutDashboard },
  { name: "Oversight Flow Simulator", href: "/simulation", icon: GitBranch },
  { name: "Signal Inbox", href: "/intake", icon: Inbox },
  { name: "Cases", href: "/cases", icon: FileSearch },
  { name: "Tickets", href: "/tickets", icon: ClipboardList },
  { name: "Risk Prioritization", href: "/scoring", icon: ShieldAlert },
  { name: "Nutrition & Cost", href: "/nutrition", icon: Activity },
  { name: "Regional Heatmap", href: "/heatmap", icon: Map },
  { name: "Vendor Watchlist", href: "/vendors", icon: Factory },
  { name: "Governance Log", href: "/audit-trail", icon: History },
  { name: "AI Case Copilot", href: "/copilot", icon: Bot },
];

export default function MobileNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  return (
    <div className="lg:hidden">
      <button
        onClick={() => setOpen((current) => !current)}
        className="rounded-md p-2 -ml-2 transition-colors hover:bg-surface-raised"
        aria-label={open ? "Close navigation" : "Open navigation"}
      >
        {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </button>
      {open ? (
        <div className="absolute left-4 right-4 top-16 z-50 max-h-[calc(100dvh-5rem)] overflow-y-auto rounded-xl border border-border bg-surface-raised p-3 shadow-xl">
          <nav className="grid grid-cols-1 gap-1 sm:grid-cols-2">
            {mobileItems.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className={cn(
                    "flex min-w-0 items-center gap-3 rounded-md px-3 py-3 text-sm font-medium transition-colors",
                    active
                      ? "bg-brand-500/10 text-brand-200"
                      : "text-muted-foreground hover:bg-surface hover:text-foreground",
                  )}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  <span className="min-w-0 break-words">{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      ) : null}
    </div>
  );
}
