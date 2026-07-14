import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { FindingList } from "./FindingList";
import { useQualityReport } from "./useQualityReport";

export function ReviewDashboard() {
  const { report, loading, error } = useQualityReport();
  if (loading) return <Loading label="Loading review…" />;
  if (error) return <ErrorNotice message={error} />;
  const gate = report?.gate;
  const arch = (report?.review_findings ?? []).filter((f) => f.engine === "architecture");
  const code = (report?.review_findings ?? []).filter((f) => f.engine === "code");

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Review Dashboard</h1>
          <p>Architecture + code quality review across the generated implementation.</p>
        </div>
      </div>

      <div className="grid stats span-all">
        <StatCard
          label="Architecture"
          value={gate ? gate.architecture_score.toFixed(0) : "—"}
          accent={gate && gate.architecture_score >= 90 ? "ok" : "warn"}
        />
        <StatCard label="Code" value={gate ? gate.code_score.toFixed(0) : "—"} />
        <StatCard label="Documentation" value={gate ? gate.documentation_score.toFixed(0) : "—"} />
        <StatCard label="Overall" value={gate ? gate.overall_score.toFixed(0) : "—"} accent="ok" />
      </div>

      <SectionCard title="Architecture Review">
        <FindingList findings={arch} emptyMessage="No architecture issues — clean layering." />
      </SectionCard>

      <SectionCard title="Code Review">
        <FindingList findings={code} emptyMessage="No code-quality issues detected." />
      </SectionCard>

      <SectionCard title="Documentation Review">
        <FindingList
          findings={report?.documentation_findings ?? []}
          emptyMessage="Documentation complete."
        />
      </SectionCard>
    </div>
  );
}
