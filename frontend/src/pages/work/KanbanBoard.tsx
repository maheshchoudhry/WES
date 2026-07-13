import { Link } from "react-router-dom";

import { workApi, type KanbanColumn } from "../../api/work";
import { ErrorNotice, Loading } from "../../components/States";
import { useAsync } from "../../hooks/useAsync";

const COLUMN_LABEL: Record<string, string> = {
  backlog: "Backlog",
  planned: "Planned",
  assigned: "Assigned",
  in_progress: "In Progress",
  review: "Review",
  testing: "Testing",
  done: "Done",
};

export function KanbanBoard() {
  const { data, loading, error, reload } = useAsync<KanbanColumn[]>(
    () => workApi.kanban().then((r) => r.data),
    [],
  );

  if (loading) return <Loading label="Loading board…" />;
  if (error) return <ErrorNotice message={error} />;
  const columns = data ?? [];

  async function move(taskId: string, status: string) {
    try {
      await workApi.updateTask(taskId, { status });
      reload();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Move failed");
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Task Board</h1>
          <p>Kanban view of all work items. Move a card with its status selector.</p>
        </div>
      </div>

      <div className="kanban" role="list">
        {columns.map((col) => (
          <div className="kanban-col" role="listitem" key={col.status}>
            <div className="kanban-col-head">
              <span>{COLUMN_LABEL[col.status] ?? col.status}</span>
              <span className="kanban-count">{col.count}</span>
            </div>
            <div className="kanban-cards">
              {col.tasks.map((t) => (
                <div className="kanban-card" key={t.id}>
                  <div className="kanban-card-code">{t.task_code}</div>
                  <Link to={`/tasks/${t.id}`} className="kanban-card-title">
                    {t.title}
                  </Link>
                  <div className="kanban-card-meta">
                    <span className={`badge prio-${t.priority}`}>{t.priority}</span>
                    <span className="muted">{t.assigned_name ?? "Unassigned"}</span>
                  </div>
                  <select
                    aria-label={`Move ${t.task_code}`}
                    className="kanban-move"
                    value={t.status}
                    onChange={(e) => move(t.id, e.target.value)}
                  >
                    {Object.keys(COLUMN_LABEL).map((s) => (
                      <option key={s} value={s}>
                        {COLUMN_LABEL[s]}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
