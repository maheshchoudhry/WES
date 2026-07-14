import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { FindingList } from "./FindingList";
import { useQualityReport } from "./useQualityReport";

export function PerformanceDashboard() {
  const { dash, report, loading, error } = useQualityReport();
  if (loading) return <Loading label="Loading performance review…" />;
  if (error) return <ErrorNotice message={error} />;
  const gate = report?.gate;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Performance Dashboard</h1>
          <p>Automated performance analysis: nested loops, N+1 queries, DB calls in loops.</p>
        </div>
      </div>

      <div className="grid stats span-all">
        <StatCard
          label="Performance Score"
          value={gate ? gate.performance_score.toFixed(0) : "—"}
          accent={gate && gate.performance_score >= 90 ? "ok" : "warn"}
        />
        <StatCard
          label="Avg Performance"
          value={dash ? dash.avg_performance_score.toFixed(0) : "—"}
        />
        <StatCard label="Findings" value={report?.performance_findings.length ?? 0} />
        <StatCard label="Dependency Findings" value={report?.dependency_findings.length ?? 0} />
      </div>

      <SectionCard title="Performance Findings">
        <FindingList
          findings={report?.performance_findings ?? []}
          emptyMessage="No performance issues detected."
        />
      </SectionCard>

      <SectionCard title="Dependency Findings">
        <FindingList
          findings={report?.dependency_findings ?? []}
          emptyMessage="No dependency issues detected."
        />
      </SectionCard>
    </div>
  );
}
