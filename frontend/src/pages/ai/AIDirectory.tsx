import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { aiApi, type AIDepartment, type AIEmployee } from "../../api/ai";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

async function load(): Promise<{ employees: AIEmployee[]; departments: AIDepartment[] }> {
  const [employees, departments] = await Promise.all([aiApi.listEmployees(), aiApi.departments()]);
  return { employees: employees.data, departments: departments.data };
}

export function AIDirectory() {
  const { data, loading, error } = useAsync(load, []);
  const [search, setSearch] = useState("");
  const [dept, setDept] = useState("");

  const filtered = useMemo(() => {
    let list = data?.employees ?? [];
    if (dept) list = list.filter((e) => e.department_id === dept);
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (e) => e.name.toLowerCase().includes(q) || e.employee_code.toLowerCase().includes(q),
      );
    }
    return list;
  }, [data, search, dept]);

  if (loading) return <Loading label="Loading directory…" />;
  if (error) return <ErrorNotice message={error} />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>AI Employee Directory</h1>
          <p>All AI employees in the organization.</p>
        </div>
      </div>

      <div
        className="card"
        style={{ display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap" }}
      >
        <input
          aria-label="Search AI employees"
          placeholder="Search by name or code…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ flex: 1, minWidth: 200 }}
        />
        <select
          aria-label="Filter by department"
          value={dept}
          onChange={(e) => setDept(e.target.value)}
        >
          <option value="">All departments</option>
          {(data?.departments ?? []).map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
      </div>

      {filtered.length === 0 ? (
        <Empty message="No AI employees match your filters." />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Role</th>
                <th>Department</th>
                <th>Manager</th>
                <th>Authority</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((e) => (
                <tr key={e.id}>
                  <td>{e.employee_code}</td>
                  <td>
                    <Link to={`/ai/employees/${e.id}`}>{e.name}</Link>
                  </td>
                  <td>{e.role_title}</td>
                  <td>{e.department_name}</td>
                  <td>{e.manager_name ?? "—"}</td>
                  <td style={{ textTransform: "capitalize" }}>{e.authority}</td>
                  <td>
                    <StatusBadge status={e.status} />
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
