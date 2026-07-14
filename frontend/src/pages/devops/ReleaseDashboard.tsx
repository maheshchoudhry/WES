import { devopsApi, type ReleaseVersion } from "../../api/devops";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

export function ReleaseDashboard() {
  const { data, loading, error } = useAsync<ReleaseVersion[]>(
    () => devopsApi.releases().then((r) => r.data),
    [],
  );
  if (loading) return <Loading label="Loading releases…" />;
  if (error) return <ErrorNotice message={error} />;
  const releases = data ?? [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Release Dashboard</h1>
          <p>Version history, release notes, and deployment status per release.</p>
        </div>
      </div>

      {releases.length === 0 ? (
        <Empty message="No releases yet." />
      ) : (
        releases.map((r) => (
          <SectionCard
            key={r.id}
            title={`${r.version} (${r.channel})`}
            action={<StatusBadge status={r.status === "released" ? "active" : "onboarding"} />}
          >
            {r.notes && (
              <>
                <p className="muted">{r.notes.summary}</p>
                <div className="quick-actions" style={{ marginBottom: 8 }}>
                  {r.notes.changes.map((c) => (
                    <span key={c} className="badge prio-low">
                      {c}
                    </span>
                  ))}
                </div>
              </>
            )}
            <div className="quick-actions">
              {r.deployments.length === 0 ? (
                <span className="muted">Not deployed.</span>
              ) : (
                r.deployments.map((d, i) => (
                  <span
                    key={i}
                    className={`badge ${d.status === "deployed" ? "badge-active" : "prio-medium"}`}
                  >
                    {d.environment}: {d.status}
                  </span>
                ))
              )}
            </div>
          </SectionCard>
        ))
      )}
    </div>
  );
}
