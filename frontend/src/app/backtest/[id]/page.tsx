"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { MetricCard } from "@/components/MetricCard";
import { EquityChart } from "@/components/EquityChart";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  ResponsiveContainer,
  CartesianGrid,
  Tooltip,
} from "recharts";

type Report = {
  id: string;
  metrics: Record<string, number | string>;
  equity_curve: { time: string; equity: number }[];
  drawdown_curve: { time: string; drawdown_pct: number }[];
  trades: { entry_time: string; exit_time: string; pnl: number; entry_price: number; exit_price: number }[];
};

export default function BacktestPage() {
  const params = useParams();
  const strategyId = params.id as string;
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<Report[]>([]);

  const loadHistory = useCallback(() => {
    api<{ reports: Report[] }>(`/api/strategies/${strategyId}/backtests`).then((d) => {
      setHistory(d.reports);
      if (d.reports[0]) setReport(d.reports[0]);
    });
  }, [strategyId]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  async function runBacktest() {
    setLoading(true);
    try {
      const res = await api<{ report: Report }>(`/api/strategies/${strategyId}/backtest`, { method: "POST" });
      setReport(res.report);
      loadHistory();
    } finally {
      setLoading(false);
    }
  }

  function downloadReport() {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `backtest-${report.id}.json`;
    a.click();
  }

  const m = report?.metrics || {};

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-xl font-bold text-white">Backtesting</h1>
        <div className="flex gap-2">
          <button className="btn-primary" onClick={runBacktest} disabled={loading}>
            {loading ? "Running on cloud…" : "Run Backtest"}
          </button>
          {report && (
            <button className="btn-secondary" onClick={downloadReport}>
              Download JSON
            </button>
          )}
          <Link href={`/live?strategy=${strategyId}`} className="btn-secondary">
            Deploy Live
          </Link>
        </div>
      </div>

      {history.length > 1 && (
        <select
          className="input max-w-xs"
          onChange={(e) => {
            const r = history.find((h) => h.id === e.target.value);
            if (r) setReport(r);
          }}
        >
          {history.map((h) => (
            <option key={h.id} value={h.id}>
              Run {h.id.slice(0, 8)} — {String(h.metrics.total_return_pct)}%
            </option>
          ))}
        </select>
      )}

      {report ? (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <MetricCard label="Total Return" value={`${m.total_return_pct}%`} />
            <MetricCard label="Win Rate" value={`${m.win_rate}%`} />
            <MetricCard label="Trades" value={String(m.num_trades)} />
            <MetricCard label="Max Drawdown" value={`${m.max_drawdown_pct}%`} />
            <MetricCard label="Avg Profit" value={String(m.avg_profit)} />
            <MetricCard label="Avg Loss" value={String(m.avg_loss)} />
            <MetricCard label="Final Equity" value={String(m.final_equity)} />
            <MetricCard label="Type" value={String(m.strategy_type)} />
          </div>

          <div className="card">
            <h3 className="mb-2 font-semibold">Equity Curve</h3>
            <EquityChart data={report.equity_curve} />
          </div>

          <div className="card">
            <h3 className="mb-2 font-semibold">Drawdown</h3>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={report.drawdown_curve.filter((_, i) => i % 5 === 0)}>
                  <CartesianGrid stroke="#334155" />
                  <XAxis dataKey="time" tick={false} />
                  <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} />
                  <Tooltip contentStyle={{ background: "#1e293b" }} />
                  <Line type="monotone" dataKey="drawdown_pct" stroke="#f87171" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="card overflow-x-auto">
            <h3 className="mb-2 font-semibold">Trade Log</h3>
            <table className="w-full text-left text-xs">
              <thead className="text-slate-500">
                <tr>
                  <th className="p-2">Entry</th>
                  <th className="p-2">Exit</th>
                  <th className="p-2">PnL</th>
                </tr>
              </thead>
              <tbody>
                {report.trades.map((t, i) => (
                  <tr key={i} className="border-t border-slate-700">
                    <td className="p-2">{t.entry_time}</td>
                    <td className="p-2">{t.exit_time}</td>
                    <td className={`p-2 ${t.pnl >= 0 ? "text-profit" : "text-loss"}`}>{t.pnl}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <p className="text-sm text-slate-500">Run a backtest to see results. Unlimited runs supported.</p>
      )}
    </div>
  );
}
