import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: ReactNode;
  hint?: string;
  accent?: "default" | "ok" | "warn" | "muted";
}

/** Reusable statistic tile. Used across the dashboard and future modules. */
export function StatCard({ label, value, hint, accent = "default" }: StatCardProps) {
  return (
    <div className={`card stat stat-${accent}`}>
      <div className="value">{value}</div>
      <div className="label">{label}</div>
      {hint && <div className="stat-hint">{hint}</div>}
    </div>
  );
}
