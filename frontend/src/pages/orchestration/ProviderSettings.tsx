import { orchestrationApi, type Provider } from "../../api/orchestration";
import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

const HEALTH: Record<string, string> = {
  healthy: "active",
  degraded: "onboarding",
  unavailable: "inactive",
  unknown: "inactive",
};

async function load(): Promise<{ providers: Provider[]; mappings: Record<string, string> }> {
  const [providers, mappings] = await Promise.all([
    orchestrationApi.providers(),
    orchestrationApi.roleMappings(),
  ]);
  return { providers: providers.data, mappings: mappings.data };
}

export function ProviderSettings() {
  const { data, loading, error, reload } = useAsync(load, []);
  if (loading) return <Loading label="Loading providers…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;

  async function toggle(p: Provider) {
    await orchestrationApi.setEnabled(p.id, !p.enabled);
    reload();
  }
  async function makeDefault(p: Provider) {
    try {
      await orchestrationApi.setDefault(p.id);
      reload();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed");
    }
  }
  async function health() {
    await orchestrationApi.healthCheck();
    reload();
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>AI Providers</h1>
          <p>Enable providers, set the default, and map roles. No real API keys are stored.</p>
        </div>
        <button className="btn" onClick={health}>
          Run Health Check
        </button>
      </div>

      <SectionCard title="Providers">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Provider</th>
                <th>Model</th>
                <th>Health</th>
                <th>API Key</th>
                <th>Enabled</th>
                <th>Default</th>
              </tr>
            </thead>
            <tbody>
              {data.providers.map((p) => (
                <tr key={p.id}>
                  <td>{p.display_name}</td>
                  <td className="muted">{p.default_model ?? "—"}</td>
                  <td>
                    <StatusBadge status={HEALTH[p.health] ?? "inactive"} />
                    <span className="muted" style={{ marginLeft: 6 }}>
                      {p.health}
                    </span>
                  </td>
                  <td className="muted">{p.config.api_key ?? "—"}</td>
                  <td>
                    <input
                      type="checkbox"
                      checked={p.enabled}
                      onChange={() => toggle(p)}
                      aria-label={`Enable ${p.name}`}
                    />
                  </td>
                  <td>
                    {p.is_default ? (
                      <span className="badge badge-active">Default</span>
                    ) : (
                      <button
                        className="btn btn-sm"
                        disabled={!p.enabled}
                        onClick={() => makeDefault(p)}
                      >
                        Set default
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>

      <SectionCard title="Role → Provider Mapping">
        <ul className="activity">
          {Object.entries(data.mappings).map(([role, provider]) => (
            <li key={role}>
              <span className="activity-body">
                <span className="activity-label">{role}</span>
              </span>
              <span className="badge prio-medium">{provider}</span>
            </li>
          ))}
        </ul>
      </SectionCard>
    </div>
  );
}
