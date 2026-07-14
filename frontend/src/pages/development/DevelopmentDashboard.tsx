import { useState } from "react";
import { Link } from "react-router-dom";

import { developmentApi, type DevFounderDash } from "../../api/development";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

export function DevelopmentDashboard() {
  const { data, loading, error, reload } = useAsync<DevFounderDash>(
    () => developmentApi.founderDashboard().then((r) => r.data),
    [],
  );
  const [title, setTitle] = useState("");
  const [busy, setBusy] = useState(false);

  async function run() {
    if (title.length < 3) return;
    setBusy(true);
    try {
      await developmentApi.createAndRun(title);
      setTitle("");
      reload();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Run failed");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Loading label="Loading development…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Autonomous Development</h1>
          <p>
            Turn a task into a real implementation — plan, code, tests, review, git branch, and a
            pull request. The Founder approves; nothing is pushed or merged.
          </p>
        </div>
      </div>

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
        <input
          aria-label="Task title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && run()}
          placeholder="Describe a software task (e.g. Add a health ping utility)"
          style={{ flex: 1, minWidth: 260 }}
        />
        <button className="btn btn-primary" onClick={run} disabled={busy || title.length < 3}>
          {busy ? "Running…" : "Run Autonomous Task"}
        </button>
      </div>

      <div className="grid stats span-all">
        <StatCard label="Running" value={data.running} />
        <StatCard label="Completed" value={data.completed} accent="ok" />
        <StatCard
          label="Pending Approvals"
          value={data.pending_approvals}
          accent={data.pending_approvals > 0 ? "warn" : "ok"}
        />
        <StatCard label="Open PRs" value={data.open_pull_requests} />
      </div>

      <SectionCard
        title="Recent Tasks"
        action={
          <Link to="/development/approvals" className="btn btn-sm">
            Approval Center
          </Link>
        }
      >
        {data.recent_tasks.length === 0 ? (
          <Empty message="No development tasks yet. Run one above." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Title</th>
                  <th>Status</th>
                  <th>Branch</th>
                  <th>Duration</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_tasks.map((t) => (
                  <tr key={t.id}>
                    <td className="muted">{t.code}</td>
                    <td>
                      <Link to={`/development/tasks/${t.id}`}>{t.title}</Link>
                    </td>
                    <td>
                      <StatusBadge status={t.status} />
                    </td>
                    <td className="muted">{t.branch_name ?? "—"}</td>
                    <td>{t.duration_ms != null ? `${t.duration_ms}ms` : "—"}</td>
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
