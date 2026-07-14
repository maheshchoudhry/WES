import { executionApi, type HistoryEntry } from "../../api/execution";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

export function ExecutionHistory() {
  const { data, loading, error } = useAsync<HistoryEntry[]>(
    () => executionApi.history().then((r) => r.data),
    [],
  );
  if (loading) return <Loading label="Loading history…" />;
  if (error) return <ErrorNotice message={error} />;
  const items = data ?? [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Execution History</h1>
          <p>Output history of completed executions.</p>
        </div>
      </div>
      {items.length === 0 ? (
        <Empty message="No execution history yet." />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Employee</th>
                <th>Action</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Output</th>
              </tr>
            </thead>
            <tbody>
              {items.map((h) => (
                <tr key={h.id}>
                  <td>{h.ai_employee_name}</td>
                  <td>{h.action}</td>
                  <td>
                    <StatusBadge status={h.status} />
                  </td>
                  <td>
                    {h.duration_seconds != null ? `${Math.round(h.duration_seconds / 60)}m` : "—"}
                  </td>
                  <td className="muted">{h.output ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
