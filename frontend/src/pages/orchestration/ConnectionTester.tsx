import { useState } from "react";

import { orchestrationApi, type ConnectionResult, type Provider } from "../../api/orchestration";
import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

export function ConnectionTester() {
  const { data, loading, error } = useAsync<Provider[]>(
    () => orchestrationApi.providers().then((r) => r.data),
    [],
  );
  const [results, setResults] = useState<Record<string, ConnectionResult>>({});
  const [busy, setBusy] = useState("");

  if (loading) return <Loading label="Loading providers…" />;
  if (error) return <ErrorNotice message={error} />;
  const providers = data ?? [];

  async function test(p: Provider) {
    setBusy(p.id);
    try {
      const res = await orchestrationApi.testConnection(p.id);
      setResults((r) => ({ ...r, [p.id]: res.data }));
    } finally {
      setBusy("");
    }
  }
  async function testAll() {
    setBusy("all");
    try {
      const res = await orchestrationApi.monitor();
      const map: Record<string, ConnectionResult> = {};
      for (const p of providers) {
        const match = res.data.find((r) => r.provider === p.name);
        if (match) map[p.id] = match;
      }
      setResults(map);
    } finally {
      setBusy("");
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Connection Tester</h1>
          <p>Test live connectivity to each provider. Unconfigured providers report unavailable.</p>
        </div>
        <button className="btn" onClick={testAll} disabled={busy === "all"}>
          Test All
        </button>
      </div>

      <SectionCard title="Providers">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Provider</th>
                <th>Key</th>
                <th>Result</th>
                <th>Model</th>
                <th>Latency</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {providers.map((p) => {
                const r = results[p.id];
                return (
                  <tr key={p.id}>
                    <td>{p.display_name}</td>
                    <td>{p.name === "mock" ? "n/a" : p.has_secret ? "✓" : "—"}</td>
                    <td>
                      {r ? (
                        <StatusBadge status={r.ok ? "active" : "inactive"} />
                      ) : (
                        <span className="muted">untested</span>
                      )}
                      {r && (
                        <span className="muted" style={{ marginLeft: 6 }}>
                          {r.status}
                        </span>
                      )}
                    </td>
                    <td className="muted">{r?.model ?? "—"}</td>
                    <td>{r?.latency_ms != null ? `${r.latency_ms}ms` : "—"}</td>
                    <td>
                      <button
                        className="btn btn-sm btn-primary"
                        disabled={busy === p.id}
                        onClick={() => test(p)}
                      >
                        Test
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </SectionCard>
    </div>
  );
}
