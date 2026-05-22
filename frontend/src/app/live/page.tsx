"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { MetricCard } from "@/components/MetricCard";

type Deployment = {
  id: string;
  strategy_id: string;
  status: string;
  running_pnl: number;
  open_position: boolean;
  last_price: number;
  tick_count: number;
  host: string;
};

type Trade = { side: string; price: number; pnl: number; created_at: string };
type Log = { message: string; level: string; created_at: string };

function LiveContent() {
  const search = useSearchParams();
  const strategyId = search.get("strategy");
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [selected, setSelected] = useState<Deployment | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [logs, setLogs] = useState<Log[]>([]);
  const [deploying, setDeploying] = useState(false);

  const refresh = () => {
    api<{ deployments: Deployment[] }>("/api/deployments").then((d) => {
      const running = d.deployments.filter((x) => x.status === "running");
      setDeployments(running);
      const sel = selected
        ? d.deployments.find((x) => x.id === selected.id) || running[0]
        : running[0];
      if (sel) {
        setSelected(sel);
        api<{ deployment: Deployment; trades: Trade[] }>(`/api/deployments/${sel.id}`).then((r) => {
          setTrades(r.trades);
        });
        api<{ logs: Log[] }>(`/api/logs?deployment_id=${sel.id}&limit=30`).then((r) => setLogs(r.logs));
      }
    });
  };

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
  }, [selected?.id]);

  async function deploy() {
    if (!strategyId) return;
    setDeploying(true);
    try {
      await api(`/api/strategies/${strategyId}/deploy`, {
        method: "POST",
        body: JSON.stringify({ mode: "simulation" }),
      });
      refresh();
    } finally {
      setDeploying(false);
    }
  }

  async function stop(id: string) {
    await api(`/api/deployments/${id}/stop`, { method: "POST" });
    refresh();
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-white">Live Trading (Simulation)</h1>
      <p className="text-sm text-slate-400">
        Prices and trades update via the <strong className="text-emerald-400">Railway worker</strong> loop — continuous cloud execution.
      </p>

      {strategyId && (
        <button className="btn-primary deploy-animate" onClick={deploy} disabled={deploying}>
          {deploying ? "Deploying to cloud…" : "▶ Deploy Strategy to Cloud Worker"}
        </button>
      )}

      {selected ? (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <MetricCard label="Status" value={selected.status} />
            <MetricCard label="Last Price" value={selected.last_price} />
            <MetricCard label="Running PnL" value={selected.running_pnl.toFixed(2)} />
            <MetricCard label="Ticks" value={selected.tick_count} />
            <MetricCard label="Position" value={selected.open_position ? "OPEN" : "FLAT"} />
            <MetricCard label="Worker Host" value={selected.host} sub="Railway" />
          </div>

          <button className="btn-secondary text-sm" onClick={() => stop(selected.id)}>
            Stop Cloud Execution
          </button>

          <div className="card">
            <h3 className="mb-2 font-semibold">Live Trades</h3>
            {trades.length === 0 ? (
              <p className="text-xs text-slate-500">Waiting for worker ticks…</p>
            ) : (
              <ul className="space-y-1 text-sm">
                {trades.map((t) => (
                  <li key={t.created_at + t.side} className={t.side === "buy" ? "text-profit" : "text-slate-300"}>
                    {t.side.toUpperCase()} @ {t.price} {t.pnl ? `PnL ${t.pnl}` : ""}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="card max-h-64 overflow-y-auto">
            <h3 className="mb-2 font-semibold">Live Logs</h3>
            {logs.map((l) => (
              <p key={l.created_at + l.message} className="font-mono text-xs text-slate-400">
                [{l.level}] {l.message}
              </p>
            ))}
          </div>
        </>
      ) : (
        <p className="text-sm text-slate-500">
          {strategyId ? "Click deploy to start cloud worker." : "Select a strategy from Home or pass ?strategy=id"}
        </p>
      )}

      <div className="card">
        <h3 className="mb-2 font-semibold">Active Deployments</h3>
        <ul className="space-y-2 text-sm">
          {deployments.map((d) => (
            <li
              key={d.id}
              className="cursor-pointer rounded-lg border border-slate-700 p-2 hover:border-accent"
              onClick={() => setSelected(d)}
            >
              {d.id.slice(0, 8)} · {d.status} · ₹{d.last_price} · PnL {d.running_pnl.toFixed(2)}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default function LivePage() {
  return (
    <Suspense fallback={<p className="text-slate-500">Loading…</p>}>
      <LiveContent />
    </Suspense>
  );
}
