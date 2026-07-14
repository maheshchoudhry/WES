import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useQualityReport } from "./useQualityReport";

export function ReleaseReadinessDashboard() {
  const { dash, report, loading, error } = useQualityReport();
  if (loading) return <Loading label="Loading release readiness…" />;
  if (error) return <ErrorNotice message={error} />;
  const rr = report?.release_readiness;
  const gate = report?.gate;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Release Readiness Dashboard</h1>
          <p>Whether the latest implementation is cleared for Founder approval.</p>
        </div>
      </div>

      <div className="grid stats span-all">
        <StatCard
          label="Status"
          value={rr ? <StatusBadge status={rr.status} /> : "—"}
          accent={rr?.ready ? "ok" : "warn"}
        />
        <StatCard label="Score" value={rr ? rr.score.toFixed(0) : "—"} accent="ok" />
        <StatCard label="Release Ready (all)" value={dash?.release_ready ?? 0} accent="ok" />
        <StatCard
          label="Approval Eligible"
          value={gate ? (gate.approval_eligible ? "Yes" : "No") : "—"}
          accent={gate?.approval_eligible ? "ok" : "warn"}
        />
      </div>

      <SectionCard title="Readiness Summary">
        <p>{rr?.summary ?? "No release readiness computed yet."}</p>
      </SectionCard>

      <SectionCard title="Blockers">
        {!rr || rr.blockers.length === 0 ? (
          <Empty message="No blockers — release-ready." />
        ) : (
          <ul className="activity">
            {rr.blockers.map((b, i) => (
              <li key={i}>
                <span className="activity-body">
                  <span className="activity-label">{b}</span>
                </span>
                <span className="badge prio-high">blocker</span>
              </li>
            ))}
          </ul>
        )}
      </SectionCard>

      {gate && (
        <SectionCard title="Gate Checklist">
          <div className="quick-actions">
            {gate.gates.map((g) => (
              <span key={g.code} className={`badge ${g.passed ? "badge-active" : "prio-critical"}`}>
                {g.name}: {g.passed ? "✓" : "✗"}
              </span>
            ))}
          </div>
        </SectionCard>
      )}
    </div>
  );
}
