"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Strategy = { id: string; name: string; status: string; config_json: { strategy_type: string } };

export default function HomePage() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);

  useEffect(() => {
    api<{ strategies: Strategy[] }>("/api/strategies").then((d) => setStrategies(d.strategies)).catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      <section className="card deploy-animate">
        <h1 className="text-2xl font-bold text-white">Cloud Algo Trading</h1>
        <p className="mt-2 text-sm text-slate-400">
          Describe strategies in English. AI converts to safe JSON templates. Backtests and live simulation
          execute on <strong className="text-emerald-400">Railway cloud workers</strong> — not your phone or laptop.
        </p>
        <div className="flex gap-3 mt-4">
          <Link href="/chat" className="btn-primary inline-block">
            💬 Chat Builder
          </Link>
          <Link href="/strategies/new" className="btn-secondary inline-block">
            📝 Form Builder
          </Link>
        </div>
      </section>

      <section className="grid gap-3 sm:grid-cols-3">
        {[
          { title: "💬 Chat Mode", desc: "Talk naturally about your strategy" },
          { title: "🔄 AI Parsing", desc: "Gemini converts to safe JSON templates" },
          { title: "📊 Deploy", desc: "Backtest, then run on Railway workers" },
        ].map((s) => (
          <div key={s.title} className="card">
            <h3 className="font-semibold text-white">{s.title}</h3>
            <p className="mt-1 text-xs text-slate-500">{s.desc}</p>
          </div>
        ))}
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Your Strategies</h2>
        {strategies.length === 0 ? (
          <p className="text-sm text-slate-500">No strategies yet. Create one to get started.</p>
        ) : (
          <ul className="space-y-2">
            {strategies.map((s) => (
              <li key={s.id} className="card flex items-center justify-between gap-2">
                <div>
                  <p className="font-medium text-white">{s.name}</p>
                  <p className="text-xs text-slate-500">
                    {s.config_json.strategy_type} · {s.status}
                  </p>
                </div>
                <div className="flex shrink-0 gap-2">
                  <Link href={`/backtest/${s.id}`} className="btn-secondary text-xs">
                    Backtest
                  </Link>
                  <Link href={`/live?strategy=${s.id}`} className="btn-primary text-xs">
                    Live
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
