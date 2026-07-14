import { devopsApi, type EnvironmentProfile } from "../../api/devops";
import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { useAsync } from "../../hooks/useAsync";

export function EnvironmentDashboard() {
  const { data, loading, error } = useAsync<EnvironmentProfile[]>(
    () => devopsApi.environments().then((r) => r.data),
    [],
  );
  if (loading) return <Loading label="Loading environments…" />;
  if (error) return <ErrorNotice message={error} />;
  const envs = data ?? [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Environment Dashboard</h1>
          <p>Deployment environments, strategies, and approval gates.</p>
        </div>
      </div>

      <div className="grid dept-grid">
        {envs.map((e) => (
          <SectionCard key={e.id} title={e.display_name}>
            <div className="grid stats">
              <StatCard label="Strategy" value={e.strategy.replace(/_/g, " ")} />
              <StatCard
                label="Approval"
                value={e.requires_approval ? "Required" : "Auto"}
                accent={e.requires_approval ? "warn" : "ok"}
              />
              <StatCard label="Active" value={e.active ? "Yes" : "No"} />
            </div>
            <div className="quick-actions" style={{ marginTop: 8 }}>
              {Object.entries(e.variables).map(([k, v]) => (
                <span key={k} className="badge prio-low">
                  {k}={v}
                </span>
              ))}
            </div>
          </SectionCard>
        ))}
      </div>
    </div>
  );
}
