"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

type Point = { time: string; equity: number };

export function EquityChart({ data, color = "#4ade80" }: { data: Point[]; color?: string }) {
  const sampled = data.filter((_, i) => i % Math.max(1, Math.floor(data.length / 80)) === 0);
  return (
    <div className="h-56 w-full sm:h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={sampled}>
          <CartesianGrid stroke="#334155" strokeDasharray="3 3" />
          <XAxis dataKey="time" tick={false} />
          <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} domain={["auto", "auto"]} />
          <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #475569" }} />
          <Line type="monotone" dataKey="equity" stroke={color} dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
