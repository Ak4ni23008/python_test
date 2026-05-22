"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

type Deployment = {
  id: string;
  strategy_id: string;
  status: string;
  mode: string;
  host: string;
  running_pnl: number;
  tick_count: number;
  started_at: string | null;
};

export default function DeploymentsPage() {
  const [deployments, setDeployments] = useState<Deployment[]>([]);

  useEffect(() => {
    const load = () => api<{ deployments: Deployment[] }>("/api/deployments").then((d) => setDeployments(d.deployments));
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-white">Deployment Status</h1>
      <p className="text-sm text-slate-400">All strategies deployed to Railway cloud workers.</p>

      {deployments.length === 0 ? (
        <p className="text-slate-500">No deployments yet.</p>
      ) : (
        <div className="grid gap-3">
          {deployments.map((d) => (
            <div
              key={d.id}
              className={`card deploy-animate ${d.status === "running" ? "border-emerald-700" : "border-slate-700"}`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-mono text-sm text-white">{d.id.slice(0, 12)}…</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {d.mode} · {d.host} · {d.tick_count} ticks
                  </p>
                </div>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    d.status === "running" ? "bg-emerald-900 text-emerald-300" : "bg-slate-800 text-slate-400"
                  }`}
                >
                  {d.status}
                </span>
              </div>
              <p className="mt-2 text-lg font-bold text-profit">PnL {d.running_pnl.toFixed(2)}</p>
              <Link href={`/live?strategy=${d.strategy_id}`} className="mt-2 inline-block text-xs text-accent">
                Monitor →
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
