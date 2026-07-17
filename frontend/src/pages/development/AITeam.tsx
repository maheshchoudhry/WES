import { developmentApi, type AIAgent } from "../../api/development";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { useAsync } from "../../hooks/useAsync";

/** AI Team (WP7) — the acting AI employees that perform the development workflow,
 * each with responsibilities, decision rules, authority, and a selected provider. */
export function AITeam() {
  const { data, loading, error } = useAsync<AIAgent[]>(
    () => developmentApi.team().then((r) => r.data),
    [],
  );
  if (loading) return <Loading label="Loading AI team…" />;
  if (error) return <ErrorNotice message={error} />;
  const team = data ?? [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>AI Engineering Team</h1>
          <p>Real AI employees that perform each stage — not role labels.</p>
        </div>
      </div>

      {team.length === 0 ? (
        <Empty message="No AI employees found." />
      ) : (
        <div className="dept-grid">
          {team.map((a) => (
            <SectionCard
              key={a.employee_code}
              title={a.employee}
              action={<span className="badge prio-low">{a.provider}</span>}
            >
              <div className="agent-meta">
                <span className="badge badge-active">{a.role}</span>
                <span className="badge prio-medium" style={{ textTransform: "capitalize" }}>
                  {a.authority}
                </span>
              </div>
              {a.responsibilities.length > 0 && (
                <>
                  <div className="cmd-subhead" style={{ marginTop: 12 }}>
                    Responsibilities
                  </div>
                  <ul className="plain-list">
                    {a.responsibilities.slice(0, 4).map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </>
              )}
              <div className="cmd-subhead" style={{ marginTop: 12 }}>
                Decision Rules
              </div>
              <ul className="plain-list">
                {a.decision_rules.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </SectionCard>
          ))}
        </div>
      )}
    </div>
  );
}
