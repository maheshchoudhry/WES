import { useState } from "react";

import { orchestrationApi, type ConnectionResult, type Provider } from "../../api/orchestration";
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
  const [secretDraft, setSecretDraft] = useState<Record<string, string>>({});
  const [results, setResults] = useState<Record<string, ConnectionResult>>({});
  const [busy, setBusy] = useState("");

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
  async function saveSecret(p: Provider) {
    const value = secretDraft[p.id];
    if (!value || value.length < 8) return alert("Enter a key of at least 8 characters");
    setBusy(p.id);
    try {
      await orchestrationApi.setSecret(p.id, value);
      setSecretDraft((d) => ({ ...d, [p.id]: "" }));
      reload();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy("");
    }
  }
  async function test(p: Provider) {
    setBusy(p.id);
    try {
      const res = await orchestrationApi.testConnection(p.id);
      setResults((r) => ({ ...r, [p.id]: res.data }));
    } finally {
      setBusy("");
    }
  }
  async function selectModel(p: Provider, code: string) {
    await orchestrationApi.setActiveModel(p.id, code);
    reload();
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>AI Providers</h1>
          <p>
            Configure live providers. Enter an API key and WES executes through it — no architecture
            change. Keys are encrypted at rest and never shown.
          </p>
        </div>
        <button className="btn" onClick={() => orchestrationApi.monitor().then(reload)}>
          Monitor All
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
                <th>Priority</th>
                <th>Enabled</th>
                <th>Default</th>
              </tr>
            </thead>
            <tbody>
              {data.providers.map((p) => (
                <tr key={p.id}>
                  <td>{p.display_name}</td>
                  <td>
                    {p.models && p.models.length > 0 ? (
                      <select
                        aria-label={`Model for ${p.name}`}
                        value={p.active_model ?? p.default_model ?? ""}
                        onChange={(e) => selectModel(p, e.target.value)}
                      >
                        {p.models.map((m) => (
                          <option key={m.id} value={m.code}>
                            {m.display_name}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <span className="muted">{p.active_model ?? p.default_model ?? "—"}</span>
                    )}
                  </td>
                  <td>
                    <StatusBadge status={HEALTH[p.health] ?? "inactive"} />
                    <span className="muted" style={{ marginLeft: 6 }}>
                      {p.health}
                    </span>
                  </td>
                  <td>
                    {p.name === "ollama" ? (
                      <span className="muted">local</span>
                    ) : p.has_secret ? (
                      <span className="badge badge-active">{p.secret_hint ?? "set"}</span>
                    ) : (
                      <span className="muted">not set</span>
                    )}
                  </td>
                  <td>{p.priority}</td>
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

      <SectionCard title="Credentials & Connection">
        <p className="muted">
          Enter each provider&apos;s API key (encrypted at rest, shown masked). Test the live
          connection.
        </p>
        <div style={{ display: "grid", gap: 10 }}>
          {data.providers
            .filter((p) => p.name !== "mock")
            .map((p) => (
              <div
                key={p.id}
                style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}
              >
                <strong style={{ minWidth: 140 }}>{p.display_name}</strong>
                <input
                  aria-label={`API key for ${p.name}`}
                  type="password"
                  placeholder={p.has_secret ? (p.secret_hint ?? "••••") : "Enter API key"}
                  value={secretDraft[p.id] ?? ""}
                  onChange={(e) => setSecretDraft((d) => ({ ...d, [p.id]: e.target.value }))}
                  style={{ flex: 1, minWidth: 180 }}
                />
                <button
                  className="btn btn-sm"
                  disabled={busy === p.id}
                  onClick={() => saveSecret(p)}
                >
                  Save Key
                </button>
                <button
                  className="btn btn-sm btn-primary"
                  disabled={busy === p.id}
                  onClick={() => test(p)}
                >
                  Test
                </button>
                {results[p.id] && (
                  <span className={`badge ${results[p.id].ok ? "badge-active" : "prio-high"}`}>
                    {results[p.id].status}
                    {results[p.id].latency_ms != null ? ` · ${results[p.id].latency_ms}ms` : ""}
                  </span>
                )}
              </div>
            ))}
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
