"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  MessageSquareWarning,
  FileText,
  Camera,
  Activity,
  ShieldAlert,
  Bot,
} from "lucide-react";

const navItems = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Complaints", href: "/complaints", icon: MessageSquareWarning },
  { name: "Official Reports", href: "/reports", icon: FileText },
  { name: "Daily Reports", href: "/daily-reports", icon: Camera },
  { name: "Nutrition", href: "/nutrition", icon: Activity },
  { name: "Scoring", href: "/scoring", icon: ShieldAlert },
  { name: "AI Copilot", href: "/copilot", icon: Bot },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex w-64 flex-col bg-surface border-r border-border">
      <div className="flex items-center h-16 px-6 border-b border-border shrink-0">
        <Link href="/" className="flex items-center gap-2">
          <ShieldAlert className="h-6 w-6 text-brand-500" />
          <span className="font-bold text-lg tracking-tight">MonitorMBG</span>
        </Link>
      </div>
      <div className="flex-1 overflow-y-auto py-6 px-4">
        <nav className="flex flex-col gap-2">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  isActive
                    ? "bg-brand-500/10 text-brand-500"
                    : "text-muted-foreground hover:bg-surface-raised hover:text-foreground"
                )}
              >
                <Icon className={cn("h-4 w-4", isActive ? "text-brand-500" : "")} />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
