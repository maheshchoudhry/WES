import { useState } from "react";
import { Link } from "react-router-dom";

import { aiApi } from "../../api/ai";
import { orchestrationApi, type Provider, type Run } from "../../api/orchestration";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

interface Data {
  runs: Run[];
  employees: { id: string; name: string; role_title: string | null }[];
  providers: Provider[];
}

async function load(): Promise<Data> {
  const [runs, employees, providers] = await Promise.all([
    orchestrationApi.runs(),
    aiApi.listEmployees(),
    orchestrationApi.providers(),
  ]);
  return { runs: runs.data, employees: employees.data as never, providers: providers.data };
}

export function Executions() {
  const { data, loading, error, reload } = useAsync(load, []);
  const [employee, setEmployee] = useState("");
  const [provider, setProvider] = useState("mock");
  const [busy, setBusy] = useState(false);

  if (loading) return <Loading label="Loading executions…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;

  const empId = employee || data.employees[0]?.id || "";

  async function run() {
    setBusy(true);
    try {
      await orchestrationApi.run({ ai_employee_id: empId, provider_name: provider });
      reload();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Run failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Executions</h1>
          <p>Provider-independent execution runs. Trigger a run through any provider.</p>
        </div>
      </div>

      <div
        className="card"
        style={{
          display: "flex",
          gap: 12,
          marginBottom: 16,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <select
          aria-label="AI employee"
          value={empId}
          onChange={(e) => setEmployee(e.target.value)}
        >
          {data.employees.map((o) => (
            <option key={o.id} value={o.id}>
              {o.name}
            </option>
          ))}
        </select>
        <select
          aria-label="Provider"
          value={provider}
          onChange={(e) => setProvider(e.target.value)}
        >
          {data.providers.map((p) => (
            <option key={p.id} value={p.name}>
              {p.display_name}
            </option>
          ))}
        </select>
        <button className="btn btn-primary" onClick={run} disabled={busy}>
          {busy ? "Running…" : "Run Execution"}
        </button>
      </div>

      {data.runs.length === 0 ? (
        <Empty message="No executions yet. Run one above." />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Employee</th>
                <th>Provider</th>
                <th>Model</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Output</th>
              </tr>
            </thead>
            <tbody>
              {data.runs.map((r) => (
                <tr key={r.id}>
                  <td>{r.ai_employee_name}</td>
                  <td>{r.provider_name}</td>
                  <td className="muted">{r.model}</td>
                  <td>
                    <StatusBadge status={r.status} />
                  </td>
                  <td>{r.duration_ms != null ? `${r.duration_ms}ms` : "—"}</td>
                  <td className="muted">
                    {r.thread_id ? (
                      <Link to={`/orchestration/threads/${r.thread_id}`}>
                        {(r.output ?? r.error ?? "").slice(0, 60)}
                      </Link>
                    ) : (
                      (r.output ?? r.error ?? "").slice(0, 60)
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
