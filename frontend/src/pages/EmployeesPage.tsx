import { useMemo, useState } from "react";

import { companiesApi } from "../api/companies";
import { departmentsApi } from "../api/departments";
import { employeesApi, type EmployeeInput } from "../api/employees";
import { Modal } from "../components/Modal";
import { Empty, ErrorNotice, Loading } from "../components/States";
import { StatusBadge } from "../components/StatusBadge";
import { useAsync } from "../hooks/useAsync";
import type { AuthorityLevel, Company, Department, Employee, EmployeeStatus } from "../types";

const AUTHORITIES: AuthorityLevel[] = ["executive", "lead", "operational"];
const STATUSES: EmployeeStatus[] = ["onboarding", "active", "inactive", "archived"];

async function loadData() {
  const [companies, departments, employees] = await Promise.all([
    companiesApi.list(),
    departmentsApi.list(),
    employeesApi.list(),
  ]);
  return {
    company: companies.data[0] ?? null,
    departments: departments.data,
    employees: employees.data,
  };
}

export function EmployeesPage() {
  const { data, loading, error, reload } = useAsync(loadData, []);
  const [editing, setEditing] = useState<Employee | null>(null);
  const [creating, setCreating] = useState(false);

  const deptById = useMemo(() => {
    const map = new Map<string, Department>();
    (data?.departments ?? []).forEach((d) => map.set(d.id, d));
    return map;
  }, [data]);

  if (loading) return <Loading />;
  if (error) return <ErrorNotice message={error} />;

  const company: Company | null = data?.company ?? null;
  const departments = data?.departments ?? [];
  const employees = data?.employees ?? [];

  async function remove(emp: Employee) {
    if (!confirm(`Delete employee "${emp.full_name}"?`)) return;
    try {
      await employeesApi.remove(emp.id);
      reload();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Delete failed");
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Employees</h1>
          <p>People registered in the company and their department assignment.</p>
        </div>
        <button className="btn btn-primary" disabled={!company} onClick={() => setCreating(true)}>
          Register Employee
        </button>
      </div>

      {!company ? (
        <Empty message="Create a company first (Company Overview)." />
      ) : employees.length === 0 ? (
        <Empty message="No employees yet. Register the first one." />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Position</th>
                <th>Department</th>
                <th>Authority</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {employees.map((e) => (
                <tr key={e.id}>
                  <td>{e.employee_code}</td>
                  <td>{e.full_name}</td>
                  <td className="muted">{e.position}</td>
                  <td>{e.department_id ? (deptById.get(e.department_id)?.name ?? "—") : "—"}</td>
                  <td style={{ textTransform: "capitalize" }}>{e.authority}</td>
                  <td>
                    <StatusBadge status={e.status} />
                  </td>
                  <td>
                    <div className="row-actions">
                      <button className="btn btn-sm" onClick={() => setEditing(e)}>
                        Edit
                      </button>
                      <button className="btn btn-sm btn-danger" onClick={() => remove(e)}>
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
        <EmployeeForm
          title="Register Employee"
          companyId={company.id}
          departments={departments}
          onClose={() => setCreating(false)}
          onSaved={() => {
            setCreating(false);
            reload();
          }}
        />
      )}
      {editing && company && (
        <EmployeeForm
          title="Edit Employee"
          companyId={company.id}
          departments={departments}
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
  departments: Department[];
  initial?: Employee;
  onClose: () => void;
  onSaved: () => void;
}

function EmployeeForm({ title, companyId, departments, initial, onClose, onSaved }: FormProps) {
  const [code, setCode] = useState(initial?.employee_code ?? "");
  const [fullName, setFullName] = useState(initial?.full_name ?? "");
  const [email, setEmail] = useState(initial?.email ?? "");
  const [position, setPosition] = useState(initial?.position ?? "");
  const [authority, setAuthority] = useState<AuthorityLevel>(initial?.authority ?? "operational");
  const [status, setStatus] = useState<EmployeeStatus>(initial?.status ?? "onboarding");
  const [departmentId, setDepartmentId] = useState<string>(initial?.department_id ?? "");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (initial) {
        await employeesApi.update(initial.id, {
          full_name: fullName,
          email,
          position,
          authority,
          status,
        });
        // Department assignment uses its dedicated endpoint.
        if ((initial.department_id ?? "") !== departmentId) {
          await employeesApi.assignDepartment(initial.id, departmentId || null);
        }
      } else {
        const input: EmployeeInput = {
          company_id: companyId,
          department_id: departmentId || null,
          employee_code: code,
          full_name: fullName,
          email,
          position,
          authority,
          status,
        };
        await employeesApi.register(input);
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
          <label htmlFor="e-code">Employee Code</label>
          <input
            id="e-code"
            value={code}
            onChange={(ev) => setCode(ev.target.value)}
            placeholder="e.g. WES-EMP-006"
            disabled={!!initial}
            required
          />
        </div>
        <div className="field">
          <label htmlFor="e-name">Full Name</label>
          <input
            id="e-name"
            value={fullName}
            onChange={(ev) => setFullName(ev.target.value)}
            required
          />
        </div>
        <div className="field">
          <label htmlFor="e-email">Email</label>
          <input
            id="e-email"
            type="email"
            value={email}
            onChange={(ev) => setEmail(ev.target.value)}
            required
          />
        </div>
        <div className="field">
          <label htmlFor="e-position">Position</label>
          <input
            id="e-position"
            value={position}
            onChange={(ev) => setPosition(ev.target.value)}
            required
          />
        </div>
        <div className="field">
          <label htmlFor="e-dept">Department</label>
          <select
            id="e-dept"
            value={departmentId}
            onChange={(ev) => setDepartmentId(ev.target.value)}
          >
            <option value="">— Unassigned —</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="e-authority">Authority</label>
          <select
            id="e-authority"
            value={authority}
            onChange={(ev) => setAuthority(ev.target.value as AuthorityLevel)}
          >
            {AUTHORITIES.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="e-status">Status</label>
          <select
            id="e-status"
            value={status}
            onChange={(ev) => setStatus(ev.target.value as EmployeeStatus)}
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
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
            {busy ? "Saving…" : "Save"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
