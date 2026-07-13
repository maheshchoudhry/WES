import { Link, useParams } from "react-router-dom";

import { aiApi, type AIEmployee } from "../../api/ai";
import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

export function AIProfile() {
  const { id = "" } = useParams();
  const { data, loading, error } = useAsync<AIEmployee>(
    () => aiApi.getEmployee(id).then((r) => r.data),
    [id],
  );

  if (loading) return <Loading label="Loading profile…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;

  const e = data;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>{e.name}</h1>
          <p>
            {e.role_title} · {e.department_name} · <StatusBadge status={e.status} />
          </p>
        </div>
        <Link to="/ai/directory" className="btn">
          Back to Directory
        </Link>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-col">
          <SectionCard title="Profile">
            <dl style={{ display: "grid", gridTemplateColumns: "150px 1fr", rowGap: 8, margin: 0 }}>
              <dt className="muted">Employee ID</dt>
              <dd style={{ margin: 0 }}>{e.employee_code}</dd>
              <dt className="muted">Role</dt>
              <dd style={{ margin: 0 }}>{e.role_title}</dd>
              <dt className="muted">Department</dt>
              <dd style={{ margin: 0 }}>{e.department_name}</dd>
              <dt className="muted">Manager</dt>
              <dd style={{ margin: 0 }}>{e.manager_name ?? "— (executive)"}</dd>
              <dt className="muted">Authority</dt>
              <dd style={{ margin: 0, textTransform: "capitalize" }}>{e.authority}</dd>
              <dt className="muted">Decision Scope</dt>
              <dd style={{ margin: 0 }}>{e.decision_scope ?? "—"}</dd>
              <dt className="muted">Version</dt>
              <dd style={{ margin: 0 }}>v{e.version}</dd>
            </dl>
          </SectionCard>

          <SectionCard title="Responsibilities">
            {e.responsibilities.length === 0 ? (
              <p className="muted">None recorded.</p>
            ) : (
              <ul>
                {e.responsibilities.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            )}
          </SectionCard>
        </div>

        <div className="dashboard-col">
          <SectionCard title="Capabilities">
            {e.capabilities.length === 0 ? (
              <p className="muted">None recorded.</p>
            ) : (
              <div className="quick-actions">
                {e.capabilities.map((c) => (
                  <span key={c.code} className="badge badge-active">
                    {c.name}
                  </span>
                ))}
              </div>
            )}
          </SectionCard>

          <SectionCard title="KPIs">
            {e.kpis.length === 0 ? (
              <p className="muted">None recorded.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>KPI</th>
                    <th>Target</th>
                  </tr>
                </thead>
                <tbody>
                  {e.kpis.map((k, i) => (
                    <tr key={i}>
                      <td>{k.name}</td>
                      <td>
                        {k.target ?? "—"}
                        {k.unit ? ` ${k.unit}` : ""}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
