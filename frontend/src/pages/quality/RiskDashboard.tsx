import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { useQualityReport } from "./useQualityReport";

function Bar({ label, value, invert }: { label: string; value: number; invert?: boolean }) {
  const good = invert ? value < 40 : value >= 70;
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <span>{label}</span>
        <strong>{value.toFixed(0)}</strong>
      </div>
      <div style={{ background: "#1e293b", borderRadius: 4, height: 8, marginTop: 4 }}>
        <div
          style={{
            width: `${Math.min(100, value)}%`,
            height: 8,
            borderRadius: 4,
            background: good ? "#4ade80" : "#f59e0b",
          }}
        />
      </div>
    </div>
  );
}

export function RiskDashboard() {
  const { report, loading, error } = useQualityReport();
  if (loading) return <Loading label="Loading risk analysis…" />;
  if (error) return <ErrorNotice message={error} />;
  const m = report?.metrics;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Risk Analysis Dashboard</h1>
          <p>Risk, impact, confidence, complexity, and maintainability of the latest change.</p>
        </div>
      </div>

      <div className="grid stats span-all">
        <StatCard
          label="Risk Score"
          value={m ? m.risk_score.toFixed(0) : "—"}
          accent={m && m.risk_score < 40 ? "ok" : "warn"}
          hint="lower is better"
        />
        <StatCard label="Confidence" value={m ? m.confidence_score.toFixed(0) : "—"} accent="ok" />
        <StatCard label="Complexity" value={m ? m.complexity_score.toFixed(0) : "—"} />
        <StatCard label="Maintainability" value={m ? m.maintainability_score.toFixed(0) : "—"} />
      </div>

      <SectionCard title="Risk Profile">
        {!m ? (
          <p className="muted">No metrics computed yet.</p>
        ) : (
          <div style={{ maxWidth: 520 }}>
            <Bar label="Risk (lower is better)" value={m.risk_score} invert />
            <Bar label="Impact (lower is better)" value={m.impact_score} invert />
            <Bar label="Confidence" value={m.confidence_score} />
            <Bar label="Complexity health" value={m.complexity_score} />
            <Bar label="Maintainability" value={m.maintainability_score} />
          </div>
        )}
      </SectionCard>
    </div>
  );
}
