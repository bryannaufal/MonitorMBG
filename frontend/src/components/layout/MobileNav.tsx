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
  { name: "Pusat Kendali", href: "/", icon: LayoutDashboard },
  // Disembunyikan sementara dari navigasi; halaman /simulation tetap ada.
  // { name: "Simulator Alur Pengawasan", href: "/simulation", icon: GitBranch },
  { name: "Kotak Masuk Sinyal", href: "/intake", icon: Inbox },
  { name: "Kasus", href: "/cases", icon: FileSearch },
  { name: "Tiket Tindak Lanjut", href: "/tickets", icon: ClipboardList },
  { name: "Penilaian Risiko", href: "/scoring", icon: ShieldAlert },
  { name: "Gizi & Biaya", href: "/nutrition", icon: Activity },
  { name: "Heatmap Wilayah", href: "/heatmap", icon: Map },
  { name: "Daftar Pantauan Vendor", href: "/vendors", icon: Factory },
  { name: "Jejak Audit", href: "/audit-trail", icon: History },
  { name: "Asisten Ringkasan Kasus", href: "/copilot", icon: Bot },
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
                      ? "bg-brand-500/10 text-brand-800 dark:text-brand-200"
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
