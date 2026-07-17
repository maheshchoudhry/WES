import { useState } from "react";
import { Link } from "react-router-dom";

import { workApi } from "../../api/work";
import { Modal } from "../../components/Modal";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

export function ProjectsPage() {
  const { data, loading, error, reload } = useAsync(
    () => workApi.projects().then((r) => r.data),
    [],
  );
  const [creating, setCreating] = useState(false);

  if (loading) return <Loading label="Loading projects…" />;
  if (error) return <ErrorNotice message={error} />;
  const projects = data ?? [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Projects</h1>
          <p>Software projects executed by the AI organization.</p>
        </div>
        <div className="quick-actions">
          <button className="btn" onClick={() => setCreating(true)}>
            Quick Add
          </button>
          <Link to="/projects/new" className="btn btn-primary">
            New Project
          </Link>
        </div>
      </div>

      {projects.length === 0 ? (
        <Empty message="No projects yet." />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Owner</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Tasks</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((p) => (
                <tr key={p.id}>
                  <td>{p.code}</td>
                  <td>
                    <Link to={`/projects/${p.id}`}>{p.name}</Link>
                  </td>
                  <td>{p.owner_name ?? "—"}</td>
                  <td>
                    <StatusBadge status={p.status} />
                  </td>
                  <td>
                    <span className={`badge prio-${p.priority}`}>{p.priority}</span>
                  </td>
                  <td>{p.task_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {creating && (
        <CreateProject
          onClose={() => setCreating(false)}
          onSaved={() => {
            setCreating(false);
            reload();
          }}
        />
      )}
    </div>
  );
}

function CreateProject({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [priority, setPriority] = useState("medium");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await workApi.createProject({ code, name, priority });
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title="New Project" onClose={onClose}>
      <form onSubmit={submit}>
        <div className="field">
          <label htmlFor="p-code">Code</label>
          <input
            id="p-code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="PROJECT-002"
            required
          />
        </div>
        <div className="field">
          <label htmlFor="p-name">Name</label>
          <input id="p-name" value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="field">
          <label htmlFor="p-priority">Priority</label>
          <select id="p-priority" value={priority} onChange={(e) => setPriority(e.target.value)}>
            {["critical", "high", "medium", "low"].map((x) => (
              <option key={x} value={x}>
                {x}
              </option>
            ))}
          </select>
        </div>
        {error && <div className="form-error">{error}</div>}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? "Saving…" : "Create"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
