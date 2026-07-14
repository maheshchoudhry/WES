import { Link, useParams } from "react-router-dom";

import { developmentApi, type DevTask } from "../../api/development";
import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

export function ImplementationViewer() {
  const { id = "" } = useParams();
  const { data, loading, error } = useAsync<DevTask>(
    () => developmentApi.task(id).then((r) => r.data),
    [id],
  );
  if (loading) return <Loading label="Loading implementation…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;
  const { plan, metrics, pull_request: pr } = data;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>{data.title}</h1>
          <p>
            {data.code} · branch <code>{data.branch_name ?? "—"}</code>
          </p>
        </div>
        <StatusBadge status={data.status} />
      </div>

      {data.error && <ErrorNotice message={data.error} />}

      {metrics && (
        <div className="grid stats span-all">
          <StatCard label="Files" value={metrics.generated_files} />
          <StatCard label="Commits" value={metrics.commits} />
          <StatCard label="Tests Passed" value={metrics.tests_passed} accent="ok" />
          <StatCard
            label="Review Score"
            value={metrics.review_score.toFixed(0)}
            accent={metrics.review_score >= 70 ? "ok" : "warn"}
          />
        </div>
      )}

      <div className="quick-actions" style={{ margin: "12px 0" }}>
        <Link to={`/development/changes/${data.id}`} className="btn btn-sm">
          Repository Changes
        </Link>
        <Link to={`/development/review/${data.id}`} className="btn btn-sm">
          Review Center
        </Link>
        <Link to={`/development/timeline/${data.id}`} className="btn btn-sm">
          Task Timeline
        </Link>
      </div>

      {plan && (
        <SectionCard title="Implementation Plan">
          <p className="muted">{plan.summary}</p>
          <p>
            <strong>Risk:</strong> {plan.risk_analysis}
          </p>
          <p>
            <strong>Architecture context:</strong> {plan.architecture_context}
          </p>
          <h4>Implementation Order</h4>
          <ol>
            {plan.implementation_order.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
          <div className="dashboard-grid">
            <div className="dashboard-col">
              <h4>Acceptance Criteria</h4>
              <ul>
                {plan.acceptance_criteria.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
              <h4>Required Knowledge</h4>
              <div className="quick-actions">
                {plan.required_knowledge.length === 0 ? (
                  <span className="muted">None</span>
                ) : (
                  plan.required_knowledge.map((k, i) => (
                    <span key={i} className="badge prio-low">
                      {k}
                    </span>
                  ))
                )}
              </div>
            </div>
            <div className="dashboard-col">
              <h4>Affected Files</h4>
              <div className="quick-actions">
                {plan.affected_files.length === 0 ? (
                  <span className="muted">New module (no existing files affected)</span>
                ) : (
                  plan.affected_files.map((f) => (
                    <span key={f} className="badge prio-low">
                      {f}
                    </span>
                  ))
                )}
              </div>
              <h4>Dependencies</h4>
              <div className="quick-actions">
                {plan.dependencies.map((d) => (
                  <span key={d} className="badge prio-low">
                    {d}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </SectionCard>
      )}

      {pr && (
        <SectionCard
          title="Pull Request Draft"
          action={
            <Link to="/development/pull-requests" className="btn btn-sm">
              PR Center
            </Link>
          }
        >
          <p>
            <strong>{pr.title}</strong> — <StatusBadge status={pr.status} />
          </p>
          <p className="muted">
            {pr.branch_name} → {pr.base_branch} · {pr.commit_count} commits · {pr.files_changed}{" "}
            files · +{pr.additions}/−{pr.deletions}
          </p>
          <pre
            className="chat-content"
            style={{ whiteSpace: "pre-wrap", maxHeight: 260, overflow: "auto" }}
          >
            {pr.body}
          </pre>
        </SectionCard>
      )}
    </div>
  );
}
