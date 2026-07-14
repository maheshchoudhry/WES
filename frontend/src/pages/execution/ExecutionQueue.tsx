import { executionApi, type QueueItem } from "../../api/execution";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

const NEXT: Record<string, string | null> = {
  queued: "in_progress",
  in_progress: "completed",
  completed: null,
  failed: null,
  cancelled: null,
};

export function ExecutionQueue() {
  const { data, loading, error, reload } = useAsync<QueueItem[]>(
    () => executionApi.queue().then((r) => r.data),
    [],
  );
  if (loading) return <Loading label="Loading execution queue…" />;
  if (error) return <ErrorNotice message={error} />;
  const items = data ?? [];

  async function advance(item: QueueItem) {
    const next = NEXT[item.status];
    if (!next) return;
    try {
      await executionApi.advanceQueue(item.id, next);
      reload();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Advance failed");
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Execution Queue</h1>
          <p>Work items queued for AI employees. Advance an item to progress it.</p>
        </div>
      </div>
      {items.length === 0 ? (
        <Empty message="Execution queue is empty." />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Employee</th>
                <th>Task</th>
                <th>Priority</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {items.map((q) => (
                <tr key={q.id}>
                  <td>{q.title}</td>
                  <td>{q.ai_employee_name}</td>
                  <td>{q.work_item_code ?? "—"}</td>
                  <td>
                    <span className={`badge prio-${q.priority}`}>{q.priority}</span>
                  </td>
                  <td>
                    <StatusBadge status={q.status} />
                  </td>
                  <td>
                    {NEXT[q.status] && (
                      <button className="btn btn-sm" onClick={() => advance(q)}>
                        → {NEXT[q.status]!.replace("_", " ")}
                      </button>
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
