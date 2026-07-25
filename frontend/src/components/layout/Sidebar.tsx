"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
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
  ShieldAlert,
} from "lucide-react";

import { cn } from "@/lib/utils";

const navGroups = [
  {
    label: "Pemantauan",
    items: [
      { name: "Pusat Kendali", href: "/", icon: LayoutDashboard },
      { name: "Simulator Alur Pengawasan", href: "/simulation", icon: GitBranch },
    ],
  },
  {
    label: "Intake",
    items: [{ name: "Kotak Masuk Sinyal", href: "/intake", icon: Inbox }],
  },
  {
    label: "Kerja Kasus",
    items: [
      { name: "Kasus", href: "/cases", icon: FileSearch },
      { name: "Tiket Tindak Lanjut", href: "/tickets", icon: ClipboardList },
    ],
  },
  {
    label: "Intelijen",
    items: [
      { name: "Penilaian Risiko", href: "/scoring", icon: ShieldAlert },
      { name: "Gizi & Biaya", href: "/nutrition", icon: Activity },
      { name: "Heatmap Wilayah", href: "/heatmap", icon: Map },
    ],
  },
  {
    label: "Pengawasan Vendor",
    items: [{ name: "Daftar Pantauan Vendor", href: "/vendors", icon: Factory }],
  },
  {
    label: "Tata Kelola",
    items: [
      { name: "Jejak Audit", href: "/audit-trail", icon: History },
      { name: "Asisten Ringkasan Kasus", href: "/copilot", icon: Bot },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-border bg-surface lg:flex">
      <div className="flex h-16 shrink-0 items-center border-b border-border px-6">
        <Link href="/" className="flex items-center gap-2">
          <ShieldAlert className="h-6 w-6 text-brand-400" />
          <div>
            <span className="block text-lg font-bold tracking-tight">MonitorMBG</span>
            <span className="block text-[11px] text-muted-foreground">Pengawasan Kasus MBG</span>
          </div>
        </Link>
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <nav className="flex flex-col gap-5">
          {navGroups.map((group) => (
            <div key={group.label}>
              <p className="px-3 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                {group.label}
              </p>
              <div className="mt-2 flex flex-col gap-1">
                {group.items.map((item) => {
                  const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={cn(
                        "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                        isActive
                          ? "bg-brand-500/10 text-brand-300"
                          : "text-muted-foreground hover:bg-surface-raised hover:text-foreground",
                      )}
                    >
                      <Icon className={cn("h-4 w-4", isActive ? "text-brand-300" : "")} />
                      {item.name}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </div>
    </aside>
  );
}
