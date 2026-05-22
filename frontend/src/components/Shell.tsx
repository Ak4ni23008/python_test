"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api, getApiUrl } from "@/lib/api";
import clsx from "clsx";

const nav = [
  { href: "/", label: "Home" },
  { href: "/chat", label: "💬 Chat" },
  { href: "/strategies/new", label: "📝 Create" },
  { href: "/live", label: "Live" },
  { href: "/deployments", label: "Deploy" },
  { href: "/logs", label: "Logs" },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const [cloud, setCloud] = useState<{ is_railway?: boolean; host?: string; gemini_configured?: boolean } | null>(null);
  const isChatPage = path === "/chat";

  useEffect(() => {
    api<{ is_railway: boolean; host: string; gemini_configured: boolean }>("/api/cloud/status")
      .then(setCloud)
      .catch(() => setCloud(null));
  }, []);

  if (isChatPage) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen pb-20">
      <header className="sticky top-0 z-50 border-b border-slate-800 bg-surface/95 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <Link href="/" className="text-lg font-bold tracking-tight text-white">
            CloudTrade
          </Link>
          <span className="hidden text-xs text-slate-500 sm:inline">{getApiUrl()}</span>
        </div>
        <nav className="mx-auto flex max-w-5xl gap-1 overflow-x-auto px-4 pb-2">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium",
                path === item.href ? "bg-accent text-white" : "text-slate-400 hover:bg-slate-800"
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </header>

      {cloud && (
        <div className="mx-auto max-w-5xl px-4 pt-3">
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
            <span className={clsx("inline-flex items-center gap-1 rounded-full px-2 py-1", cloud.is_railway ? "bg-emerald-900/50 text-emerald-300" : "bg-amber-900/40 text-amber-200")}>
              <span className="pulse-dot h-2 w-2 rounded-full bg-current" />
              {cloud.is_railway ? "Railway Cloud" : "Local API"}
            </span>
            <span>Host: {cloud.host}</span>
            <span>Gemini: {cloud.gemini_configured ? "✓" : "fallback"}</span>
          </div>
        </div>
      )}

      <main className="mx-auto max-w-5xl px-4 py-6">{children}</main>
    </div>
  );

      {cloud && (
        <div className="mx-auto max-w-5xl px-4 pt-3">
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
            <span className={clsx("inline-flex items-center gap-1 rounded-full px-2 py-1", cloud.is_railway ? "bg-emerald-900/50 text-emerald-300" : "bg-amber-900/40 text-amber-200")}>
              <span className="pulse-dot h-2 w-2 rounded-full bg-current" />
              {cloud.is_railway ? "Railway Cloud" : "Local API"}
            </span>
            <span>Host: {cloud.host}</span>
            <span>Gemini: {cloud.gemini_configured ? "✓" : "fallback"}</span>
          </div>
        </div>
      )}

      <main className="mx-auto max-w-5xl px-4 py-6">{children}</main>
    </div>
  );
}
