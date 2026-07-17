import { learningApi, type LearningRule, type LearningSummary } from "../api/learning";
import { Empty, ErrorNotice, Loading } from "../components/States";
import { SectionCard, StatCard } from "../components/widgets";
import { useAsync } from "../hooks/useAsync";

const KIND_BADGE: Record<string, string> = {
  bug_prevention: "prio-high",
  coding_standard: "prio-medium",
  architecture: "badge-active",
  lesson: "prio-low",
};

/** Self-Learning (WP9) — reusable rules the company derived from completed work
 * and applies to future tasks. All from real review/test evidence. */
export function SelfLearning() {
  const { data, loading, error } = useAsync<{ rules: LearningRule[]; summary: LearningSummary }>(
    async () => {
      const [rules, summary] = await Promise.all([
        learningApi.rules().then((r) => r.data),
        learningApi.summary().then((r) => r.data),
      ]);
      return { rules, summary };
    },
    [],
  );
  if (loading) return <Loading label="Loading learnings…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Self-Learning</h1>
          <p>Rules the company learned from completed work — and applies to future tasks.</p>
        </div>
      </div>

      <div className="grid stats" style={{ marginBottom: 16 }}>
        <StatCard label="Rules Learned" value={data.summary.total_rules} />
        <StatCard label="Applications" value={data.summary.total_applications} accent="ok" />
        <StatCard label="Rule Types" value={Object.keys(data.summary.by_kind).length} />
      </div>

      <SectionCard title={`Learned Rules (${data.rules.length})`}>
        {data.rules.length === 0 ? (
          <Empty message="No rules learned yet. Run a development task to start learning." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Kind</th>
                  <th>Rule</th>
                  <th>Occurrences</th>
                  <th>Applied</th>
                  <th>Evidence</th>
                </tr>
              </thead>
              <tbody>
                {data.rules.map((r) => (
                  <tr key={r.id}>
                    <td>
                      <span className={`badge ${KIND_BADGE[r.kind] ?? "prio-low"}`}>{r.kind}</span>
                    </td>
                    <td>{r.rule}</td>
                    <td>{r.occurrences}</td>
                    <td>{r.applied_count}</td>
                    <td className="muted">{r.evidence ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>
    </div>
  );
}
