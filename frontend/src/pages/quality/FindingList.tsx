import { type Finding, SEVERITY_BADGE } from "../../api/quality";
import { Empty } from "../../components/States";

export function FindingList({
  findings,
  emptyMessage,
}: {
  findings: Finding[];
  emptyMessage: string;
}) {
  if (findings.length === 0) return <Empty message={emptyMessage} />;
  return (
    <ul className="activity">
      {findings.map((f, i) => (
        <li key={i}>
          <span className="activity-body">
            <span className="activity-label">
              {f.category.replace(/_/g, " ")}
              {f.cwe ? ` · ${f.cwe}` : ""}
              {f.file_path ? ` — ${f.file_path}${f.line ? `:${f.line}` : ""}` : ""}
            </span>
            <span className="activity-time">{f.message}</span>
          </span>
          <span className={`badge ${SEVERITY_BADGE[f.severity] ?? "prio-low"}`}>{f.severity}</span>
        </li>
      ))}
    </ul>
  );
}
