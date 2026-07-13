import { Link } from "react-router-dom";

import { aiApi, type AIDeptView } from "../../api/ai";
import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

export function AIDepartmentView() {
  const { data, loading, error } = useAsync<AIDeptView[]>(
    () => aiApi.departmentView().then((r) => r.data),
    [],
  );

  if (loading) return <Loading label="Loading departments…" />;
  if (error) return <ErrorNotice message={error} />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>AI Departments</h1>
          <p>AI employees grouped by department.</p>
        </div>
      </div>

      <div className="grid" style={{ gap: 16 }}>
        {(data ?? []).map((d) => (
          <SectionCard key={d.id} title={`${d.name} · ${d.employee_count}`}>
            {d.focus && (
              <p className="muted" style={{ marginTop: 0 }}>
                {d.focus}
              </p>
            )}
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Name</th>
                    <th>Role</th>
                    <th>Authority</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {d.employees.map((e) => (
                    <tr key={e.id}>
                      <td>{e.employee_code}</td>
                      <td>
                        <Link to={`/ai/employees/${e.id}`}>{e.name}</Link>
                      </td>
                      <td>{e.role_title}</td>
                      <td style={{ textTransform: "capitalize" }}>{e.authority}</td>
                      <td>
                        <StatusBadge status={e.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SectionCard>
        ))}
      </div>
    </div>
  );
}
