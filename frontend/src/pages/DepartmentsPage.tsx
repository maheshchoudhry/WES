import { useState } from "react";

import { companiesApi } from "../api/companies";
import { departmentsApi, type DepartmentInput } from "../api/departments";
import { Modal } from "../components/Modal";
import { Empty, ErrorNotice, Loading } from "../components/States";
import { StatusBadge } from "../components/StatusBadge";
import { useAsync } from "../hooks/useAsync";
import type { Company, Department } from "../types";

async function loadData() {
  const [companies, departments] = await Promise.all([
    companiesApi.list(),
    departmentsApi.list(),
  ]);
  return { company: companies.data[0] ?? null, departments: departments.data };
}

export function DepartmentsPage() {
  const { data, loading, error, reload } = useAsync(loadData, []);
  const [editing, setEditing] = useState<Department | null>(null);
  const [creating, setCreating] = useState(false);

  if (loading) return <Loading />;
  if (error) return <ErrorNotice message={error} />;

  const company: Company | null = data?.company ?? null;
  const departments = data?.departments ?? [];

  async function remove(dep: Department) {
    if (!confirm(`Delete department "${dep.name}"?`)) return;
    try {
      await departmentsApi.remove(dep.id);
      reload();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Delete failed");
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Departments</h1>
          <p>Organizational units within the company.</p>
        </div>
        <button
          className="btn btn-primary"
          disabled={!company}
          onClick={() => setCreating(true)}
        >
          New Department
        </button>
      </div>

      {!company ? (
        <Empty message="Create a company first (Company Overview)." />
      ) : departments.length === 0 ? (
        <Empty message="No departments yet. Create the first one." />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Focus</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {departments.map((d) => (
                <tr key={d.id}>
                  <td>{d.code}</td>
                  <td>{d.name}</td>
                  <td className="muted">{d.focus ?? "—"}</td>
                  <td>
                    <StatusBadge status={d.status} />
                  </td>
                  <td>
                    <div className="row-actions">
                      <button className="btn btn-sm" onClick={() => setEditing(d)}>
                        Edit
                      </button>
                      <button className="btn btn-sm btn-danger" onClick={() => remove(d)}>
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {creating && company && (
        <DepartmentForm
          title="New Department"
          companyId={company.id}
          onClose={() => setCreating(false)}
          onSaved={() => {
            setCreating(false);
            reload();
          }}
        />
      )}
      {editing && company && (
        <DepartmentForm
          title="Edit Department"
          companyId={company.id}
          initial={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            reload();
          }}
        />
      )}
    </div>
  );
}

interface FormProps {
  title: string;
  companyId: string;
  initial?: Department;
  onClose: () => void;
  onSaved: () => void;
}

function DepartmentForm({ title, companyId, initial, onClose, onSaved }: FormProps) {
  const [code, setCode] = useState(initial?.code ?? "");
  const [name, setName] = useState(initial?.name ?? "");
  const [focus, setFocus] = useState(initial?.focus ?? "");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (initial) {
        await departmentsApi.update(initial.id, { code, name, focus });
      } else {
        const input: DepartmentInput = { company_id: companyId, code, name, focus };
        await departmentsApi.create(input);
      }
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title={title} onClose={onClose}>
      <form onSubmit={submit}>
        <div className="field">
          <label htmlFor="d-code">Code</label>
          <input
            id="d-code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="e.g. DEPT-02"
            required
          />
        </div>
        <div className="field">
          <label htmlFor="d-name">Name</label>
          <input id="d-name" value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="field">
          <label htmlFor="d-focus">Focus</label>
          <textarea
            id="d-focus"
            value={focus ?? ""}
            onChange={(e) => setFocus(e.target.value)}
            rows={2}
          />
        </div>
        {error && <div className="form-error">{error}</div>}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? "Saving…" : "Save"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
