import { useState } from "react";

import { devopsApi, type RollbackEntry, type ReleaseVersion } from "../../api/devops";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useSession } from "../../auth/SessionContext";
import { useAsync } from "../../hooks/useAsync";

export function RollbackDashboard() {
  const { user } = useSession();
  const [busy, setBusy] = useState(false);
  const [env, setEnv] = useState("staging");
  const [release, setRelease] = useState("");
  const { data, loading, error, reload } = useAsync<{
    history: RollbackEntry[];
    releases: ReleaseVersion[];
  }>(async () => {
    const [history, releases] = await Promise.all([
      devopsApi.rollbackHistory(),
      devopsApi.releases(),
    ]);
    return { history: history.data, releases: releases.data };
  }, []);
  const canRollback = user?.role === "founder";

  if (loading) return <Loading label="Loading rollback…" />;
  if (error) return <ErrorNotice message={error} />;
  const releases = data?.releases ?? [];
  const chosen = release || releases[0]?.id || "";

  async function rollback() {
    if (!chosen) return;
    setBusy(true);
    try {
      await devopsApi.rollback(env, chosen, "Manual rollback");
      reload();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Rollback failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Rollback Dashboard</h1>
          <p>Re-deploy a previous release to an environment (real local rollback). Founder-only.</p>
        </div>
      </div>

      {canRollback && (
        <div
          className="card"
          style={{
            display: "flex",
            gap: 12,
            marginBottom: 16,
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          <select aria-label="Environment" value={env} onChange={(e) => setEnv(e.target.value)}>
            {["staging", "production", "testing", "development"].map((x) => (
              <option key={x} value={x}>
                {x}
              </option>
            ))}
          </select>
          <select aria-label="Release" value={chosen} onChange={(e) => setRelease(e.target.value)}>
            {releases.map((r) => (
              <option key={r.id} value={r.id}>
                {r.version}
              </option>
            ))}
          </select>
          <button className="btn btn-primary" onClick={rollback} disabled={busy || !chosen}>
            Roll Back
          </button>
        </div>
      )}

      <SectionCard title="Rollback History">
        {!data || data.history.length === 0 ? (
          <Empty message="No rollbacks yet." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Environment</th>
                  <th>From</th>
                  <th>To</th>
                  <th>Status</th>
                  <th>Actor</th>
                </tr>
              </thead>
              <tbody>
                {data.history.map((h) => (
                  <tr key={h.id}>
                    <td>{h.environment}</td>
                    <td className="muted">{h.from_version ?? "—"}</td>
                    <td>{h.to_version ?? "—"}</td>
                    <td>
                      <StatusBadge status={h.status === "completed" ? "active" : "inactive"} />
                    </td>
                    <td className="muted">{h.actor}</td>
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
