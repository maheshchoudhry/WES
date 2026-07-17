import { useState } from "react";

import { auditApi, type AuditEntry } from "../api/audit";
import { Empty, ErrorNotice, Loading } from "../components/States";
import { SectionCard } from "../components/widgets";
import { useAsync } from "../hooks/useAsync";

const CAT_BADGE: Record<string, string> = {
  security: "prio-high",
  approval: "prio-medium",
  auth: "prio-low",
  action: "prio-low",
};

function fmt(at: string | null): string {
  if (!at) return "";
  try {
    return new Date(at).toLocaleString();
  } catch {
    return at;
  }
}

/** Audit Logs (WP5) — privileged actions and security events, from real records. */
export function AuditLogs() {
  const [cat, setCat] = useState("all");
  const { data, loading, error } = useAsync<AuditEntry[]>(
    () => auditApi.list().then((r) => r.data),
    [],
  );
  if (loading) return <Loading label="Loading audit log…" />;
  if (error) return <ErrorNotice message={error} />;
  const rows = (data ?? []).filter((r) => cat === "all" || r.category === cat);
  const cats = ["all", ...Array.from(new Set((data ?? []).map((r) => r.category)))];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Audit Logs</h1>
          <p>Privileged actions and security events — append-only.</p>
        </div>
        <select aria-label="Category" value={cat} onChange={(e) => setCat(e.target.value)}>
          {cats.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      <SectionCard title={`Events (${rows.length})`}>
        {rows.length === 0 ? (
          <Empty message="No audit events yet." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Category</th>
                  <th>Action</th>
                  <th>Actor</th>
                  <th>IP</th>
                  <th>Detail</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id}>
                    <td className="muted">{fmt(r.created_at)}</td>
                    <td>
                      <span className={`badge ${CAT_BADGE[r.category] ?? "prio-low"}`}>
                        {r.category}
                      </span>
                    </td>
                    <td>{r.action}</td>
                    <td className="muted">{r.actor ?? "—"}</td>
                    <td className="muted">{r.ip ?? "—"}</td>
                    <td className="muted">{r.detail ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>
    </div>
  );
}
