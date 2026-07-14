import { devopsApi, type Incident } from "../../api/devops";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { useAsync } from "../../hooks/useAsync";

const SEV: Record<string, string> = {
  critical: "prio-critical",
  warning: "prio-high",
  info: "prio-low",
};

export function IncidentDashboard() {
  const { data, loading, error, reload } = useAsync<Incident[]>(
    () => devopsApi.incidents().then((r) => r.data),
    [],
  );

  async function resolve(id: string) {
    await devopsApi.resolveIncident(id);
    reload();
  }

  if (loading) return <Loading label="Loading incidents…" />;
  if (error) return <ErrorNotice message={error} />;
  const incidents = data ?? [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Incident Dashboard</h1>
          <p>Incidents raised by monitoring and the pipeline, with recovery actions.</p>
        </div>
      </div>

      <SectionCard title={`Incidents (${incidents.length})`}>
        {incidents.length === 0 ? (
          <Empty message="No incidents — all systems nominal." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Title</th>
                  <th>Severity</th>
                  <th>Status</th>
                  <th>Recovery</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {incidents.map((i) => (
                  <tr key={i.id}>
                    <td className="muted">{i.code}</td>
                    <td>{i.title}</td>
                    <td>
                      <span className={`badge ${SEV[i.severity] ?? "prio-low"}`}>{i.severity}</span>
                    </td>
                    <td className="muted">{i.status}</td>
                    <td className="muted">{i.recovery_action}</td>
                    <td>
                      {i.status !== "resolved" && (
                        <button className="btn btn-sm" onClick={() => resolve(i.id)}>
                          Resolve
                        </button>
                      )}
                    </td>
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
