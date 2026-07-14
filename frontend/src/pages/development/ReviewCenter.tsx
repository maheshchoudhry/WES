import { Link, useParams } from "react-router-dom";

import { developmentApi, type DevTask } from "../../api/development";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

const SEV: Record<string, string> = {
  blocker: "prio-critical",
  warning: "prio-high",
  suggestion: "prio-medium",
  info: "prio-low",
};

export function ReviewCenter() {
  const { id = "" } = useParams();
  const { data, loading, error } = useAsync<DevTask>(
    () => developmentApi.task(id).then((r) => r.data),
    [id],
  );
  if (loading) return <Loading label="Loading review…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;
  const review = data.review;
  const tests = data.tests ?? [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Review Center</h1>
          <p>Automated code review + test results for {data.code}.</p>
        </div>
        <Link to={`/development/tasks/${data.id}`} className="btn">
          Back to Task
        </Link>
      </div>

      {review && (
        <div className="grid stats span-all">
          <StatCard
            label="Review Score"
            value={review.score.toFixed(0)}
            accent={review.score >= 70 ? "ok" : "warn"}
            hint="/ 100"
          />
          <StatCard label="Outcome" value={<StatusBadge status={review.outcome} />} />
          <StatCard label="Findings" value={review.comments.length} />
          <StatCard
            label="Tests"
            value={`${tests.reduce((n, t) => n + t.passed_count, 0)} passed`}
            accent="ok"
          />
        </div>
      )}

      <SectionCard title="Test Results">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Kind</th>
                <th>Command</th>
                <th>Status</th>
                <th>Passed</th>
                <th>Failed</th>
              </tr>
            </thead>
            <tbody>
              {tests.map((t, i) => (
                <tr key={i}>
                  <td>{t.kind}</td>
                  <td className="muted">
                    <code>{t.command}</code>
                  </td>
                  <td>
                    <StatusBadge status={t.status} />
                  </td>
                  <td>{t.passed_count}</td>
                  <td>{t.failed_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>

      <SectionCard title="Review Findings (7 dimensions)">
        {!review || review.comments.length === 0 ? (
          <Empty message="No findings." />
        ) : (
          <ul className="activity">
            {review.comments.map((c, i) => (
              <li key={i}>
                <span className="activity-body">
                  <span className="activity-label">
                    {c.dimension.replace(/_/g, " ")}
                    {c.file_path ? ` — ${c.file_path}` : ""}
                  </span>
                  <span className="activity-time">{c.message}</span>
                </span>
                <span className={`badge ${SEV[c.severity] ?? "prio-low"}`}>{c.severity}</span>
              </li>
            ))}
          </ul>
        )}
      </SectionCard>
    </div>
  );
}
