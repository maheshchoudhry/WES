import { useState } from "react";

import { aiApi } from "../../api/ai";
import { orchestrationApi, streamExecution, type Provider } from "../../api/orchestration";
import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { useAsync } from "../../hooks/useAsync";

interface Data {
  employees: { id: string; name: string }[];
  providers: Provider[];
}

export function StreamingViewer() {
  const { data, loading, error } = useAsync<Data>(async () => {
    const [employees, providers] = await Promise.all([
      aiApi.listEmployees(),
      orchestrationApi.providers(),
    ]);
    return { employees: employees.data as never, providers: providers.data };
  }, []);
  const [employee, setEmployee] = useState("");
  const [provider, setProvider] = useState("mock");
  const [text, setText] = useState("");
  const [status, setStatus] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [runId, setRunId] = useState<string | null>(null);

  if (loading) return <Loading label="Loading…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;
  const empId = employee || data.employees[0]?.id || "";

  async function run() {
    setText("");
    setStatus("streaming");
    setStreaming(true);
    setRunId(null);
    try {
      await streamExecution({ ai_employee_id: empId, provider_name: provider }, (type, payload) => {
        if (type === "start") setRunId((payload.run_id as string) ?? null);
        else if (type === "token") setText((t) => t + (payload.text as string));
        else if (type === "done") setStatus("completed");
        else if (type === "error") {
          setStatus("failed");
          setText((t) => t + `\n[error] ${payload.error ?? ""}`);
        }
      });
    } catch (err) {
      setStatus("failed");
      setText((t) => t + `\n[error] ${err instanceof Error ? err.message : "stream failed"}`);
    } finally {
      setStreaming(false);
    }
  }

  async function cancel() {
    if (runId) await orchestrationApi.cancelRun(runId);
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Streaming Viewer</h1>
          <p>Watch a live execution stream token-by-token (Server-Sent Events).</p>
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
        <button className="btn btn-primary" onClick={run} disabled={streaming}>
          {streaming ? "Streaming…" : "Stream Execution"}
        </button>
        <button className="btn btn-sm" onClick={cancel} disabled={!streaming || !runId}>
          Cancel
        </button>
        {status && <span className="badge prio-medium">{status}</span>}
      </div>

      <SectionCard title="Streamed Output">
        {text ? (
          <div className="chat-content" style={{ whiteSpace: "pre-wrap", minHeight: 80 }}>
            {text}
          </div>
        ) : (
          <p className="muted">Run a streaming execution to see partial tokens appear here.</p>
        )}
      </SectionCard>
    </div>
  );
}
