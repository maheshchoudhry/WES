import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { FindingList } from "./FindingList";
import { useQualityReport } from "./useQualityReport";

export function SecurityDashboard() {
  const { dash, report, loading, error } = useQualityReport();
  if (loading) return <Loading label="Loading security review…" />;
  if (error) return <ErrorNotice message={error} />;
  const gate = report?.gate;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Security Dashboard</h1>
          <p>Automated security review: secrets, injection, path traversal, unsafe calls.</p>
        </div>
      </div>

      <div className="grid stats span-all">
        <StatCard
          label="Security Score"
          value={gate ? gate.security_score.toFixed(0) : "—"}
          accent={gate && gate.security_score >= 90 ? "ok" : "warn"}
        />
        <StatCard
          label="Critical"
          value={dash?.open_critical ?? 0}
          accent={(dash?.open_critical ?? 0) > 0 ? "warn" : "ok"}
        />
        <StatCard label="Avg Security" value={dash ? dash.avg_security_score.toFixed(0) : "—"} />
        <StatCard label="Findings" value={report?.security_findings.length ?? 0} />
      </div>

      <SectionCard title="Security Findings (latest task)">
        <FindingList
          findings={report?.security_findings ?? []}
          emptyMessage="No security findings — clean."
        />
      </SectionCard>

      <SectionCard title="Compliance">
        <ul className="activity">
          {(report?.compliance ?? []).map((c, i) => (
            <li key={i}>
              <span className="activity-body">
                <span className="activity-label">{c.policy.replace(/_/g, " ")}</span>
                <span className="activity-time">{c.message}</span>
              </span>
              <span className={`badge ${c.status === "pass" ? "badge-active" : "prio-critical"}`}>
                {c.status}
              </span>
            </li>
          ))}
        </ul>
      </SectionCard>
    </div>
  );
}
