"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Log = {
  id: string;
  level: string;
  message: string;
  deployment_id: string | null;
  created_at: string;
};

export default function LogsPage() {
  const [logs, setLogs] = useState<Log[]>([]);

  useEffect(() => {
    const load = () => api<{ logs: Log[] }>("/api/logs?limit=100").then((d) => setLogs(d.logs));
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-white">Execution Logs</h1>
      <p className="text-sm text-slate-400">Cloud worker and API activity from Railway backend.</p>

      <div className="card max-h-[70vh] overflow-y-auto font-mono text-xs">
        {logs.map((l) => (
          <div key={l.id} className="border-b border-slate-800 py-2">
            <span className="text-slate-600">{l.created_at}</span>{" "}
            <span className={l.level === "error" ? "text-loss" : l.level === "trade" ? "text-profit" : "text-slate-400"}>
              [{l.level}]
            </span>{" "}
            {l.message}
          </div>
        ))}
        {logs.length === 0 && <p className="text-slate-500">No logs yet.</p>}
      </div>
    </div>
  );
}
