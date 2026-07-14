import { useState } from "react";

import { repositoryApi, type Impact } from "../../api/repository";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { useRepository } from "./useRepository";

export function ImpactAnalysis() {
  const { repo, loading, error } = useRepository();
  const [filePath, setFilePath] = useState("");
  const [result, setResult] = useState<Impact | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  if (loading) return <Loading label="Loading repository…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!repo) return <Empty message="No repository registered yet." />;

  async function analyze() {
    if (!filePath) return;
    setBusy(true);
    setErr(null);
    try {
      const res = await repositoryApi.impact(repo!.id, filePath);
      setResult(res.data);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  const List = ({ title, items }: { title: string; items: string[] }) => (
    <SectionCard title={`${title} (${items.length})`}>
      {items.length === 0 ? (
        <p className="muted">None.</p>
      ) : (
        <ul className="activity">
          {items.map((i) => (
            <li key={i}>
              <span className="activity-body">
                <span className="activity-label">{i}</span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Impact Analysis</h1>
          <p>Given a file, see what it depends on, what depends on it, and related tests/APIs.</p>
        </div>
      </div>

      <div
        className="card"
        style={{ display: "flex", gap: 12, marginBottom: 16, alignItems: "center" }}
      >
        <input
          aria-label="File path"
          value={filePath}
          onChange={(e) => setFilePath(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && analyze()}
          placeholder="e.g. external.py"
          style={{ flex: 1 }}
        />
        <button className="btn btn-primary" onClick={analyze} disabled={busy}>
          {busy ? "Analyzing…" : "Analyze"}
        </button>
      </div>

      {err && <ErrorNotice message={err} />}

      {result && (
        <>
          <div className="grid stats span-all">
            <StatCard label="Dependencies" value={result.dependencies.length} />
            <StatCard
              label="Dependents"
              value={result.dependents.length}
              accent={result.dependents.length > 0 ? "warn" : "ok"}
            />
            <StatCard label="Related Tests" value={result.related_tests.length} />
            <StatCard label="Related APIs" value={result.related_apis.length} />
          </div>
          <div className="dashboard-grid">
            <div className="dashboard-col">
              <List title="Depends On" items={result.dependencies} />
              <List title="Related Tests" items={result.related_tests} />
            </div>
            <div className="dashboard-col">
              <List title="Dependents (potential breakages)" items={result.dependents} />
              <SectionCard title={`Related APIs (${result.related_apis.length})`}>
                {result.related_apis.length === 0 ? (
                  <p className="muted">None.</p>
                ) : (
                  <ul className="activity">
                    {result.related_apis.map((a, i) => (
                      <li key={i}>
                        <span className="activity-body">
                          <span className="activity-label">{a.name}</span>
                          <span className="activity-time">{a.signature}</span>
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </SectionCard>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
