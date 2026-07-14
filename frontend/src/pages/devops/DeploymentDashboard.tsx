import { devopsApi, type Deployment } from "../../api/devops";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

export function DeploymentDashboard() {
  const { data, loading, error } = useAsync<Deployment[]>(
    () => devopsApi.deployments().then((r) => r.data),
    [],
  );
  if (loading) return <Loading label="Loading deployments…" />;
  if (error) return <ErrorNotice message={error} />;
  const deployments = data ?? [];
  const byEnv = ["development", "testing", "staging", "production"];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Deployment Dashboard</h1>
          <p>Real local deployments per environment (artifact extracted + verified).</p>
        </div>
      </div>

      {byEnv.map((env) => {
        const rows = deployments.filter((d) => d.environment === env);
        return (
          <SectionCard key={env} title={env.charAt(0).toUpperCase() + env.slice(1)}>
            {rows.length === 0 ? (
              <Empty message={`No ${env} deployments.`} />
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Version</th>
                      <th>Status</th>
                      <th>Strategy</th>
                      <th>Approved By</th>
                      <th>Duration</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((d) => (
                      <tr key={d.id}>
                        <td>{d.version}</td>
                        <td>
                          <StatusBadge status={d.status === "deployed" ? "active" : "inactive"} />
                          <span className="muted" style={{ marginLeft: 6 }}>
                            {d.status}
                          </span>
                        </td>
                        <td className="muted">{d.strategy}</td>
                        <td className="muted">{d.approved_by ?? "—"}</td>
                        <td>{d.duration_ms != null ? `${d.duration_ms}ms` : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </SectionCard>
        );
      })}
    </div>
  );
}
