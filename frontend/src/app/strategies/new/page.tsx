"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function NewStrategyPage() {
  const router = useRouter();
  const [english, setEnglish] = useState(
    "Buy when RSI crosses below 30 and sell when RSI crosses above 70"
  );
  const [name, setName] = useState("RSI Mean Reversion");
  const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");

  async function handleParse() {
    setLoading(true);
    setError("");
    try {
      const res = await api<{ strategy: { id: string }; config: Record<string, unknown>; ai_source: string }>(
        "/api/strategies/parse",
        { method: "POST", body: JSON.stringify({ english, name }) }
      );
      setConfig(res.config);
      router.push(`/backtest/${res.strategy.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-white">Create Strategy</h1>
      <p className="text-sm text-slate-400">
        Plain English is sent to <strong>Gemini on the backend only</strong>. Output is validated JSON — never raw Python.
      </p>

      <div className="card space-y-3">
        <label className="text-sm text-slate-400">Strategy name</label>
        <input className="input" value={name} onChange={(e) => setName(e.target.value)} />

        <label className="text-sm text-slate-400">Strategy in English</label>
        <textarea
          className="input min-h-[120px]"
          value={english}
          onChange={(e) => setEnglish(e.target.value)}
          placeholder="Buy when RSI is below 30..."
        />

        {error && <p className="text-sm text-loss">{error}</p>}

        <button className="btn-primary w-full sm:w-auto" onClick={handleParse} disabled={loading}>
          {loading ? "Parsing on cloud…" : "Parse with Gemini → Save"}
        </button>
      </div>

      {config && (
        <pre className="card overflow-x-auto text-xs text-emerald-300">{JSON.stringify(config, null, 2)}</pre>
      )}
    </div>
  );
}
