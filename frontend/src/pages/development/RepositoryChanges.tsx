import { Link, useParams } from "react-router-dom";

import { developmentApi, type DevTask } from "../../api/development";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

function DiffView({ diff }: { diff: string }) {
  return (
    <pre
      className="chat-content"
      style={{ whiteSpace: "pre-wrap", overflowX: "auto", fontSize: 12 }}
    >
      {diff.split("\n").map((line, i) => {
        const color =
          line.startsWith("+") && !line.startsWith("+++")
            ? "#4ade80"
            : line.startsWith("-") && !line.startsWith("---")
              ? "#f87171"
              : undefined;
        return (
          <div key={i} style={{ color }}>
            {line || " "}
          </div>
        );
      })}
    </pre>
  );
}

export function RepositoryChanges() {
  const { id = "" } = useParams();
  const { data, loading, error } = useAsync<DevTask>(
    () => developmentApi.task(id).then((r) => r.data),
    [id],
  );
  if (loading) return <Loading label="Loading changes…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;
  const changes = data.changes ?? [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Repository Changes</h1>
          <p>
            {data.code} · {changes.length} generated files on <code>{data.branch_name}</code>. Every
            change is reversible (isolated sandbox).
          </p>
        </div>
        <Link to={`/development/tasks/${data.id}`} className="btn">
          Back to Task
        </Link>
      </div>

      {changes.length === 0 ? (
        <Empty message="No changes generated." />
      ) : (
        changes.map((c) => (
          <SectionCard key={c.id} title={`${c.path}`} action={<StatusBadge status={c.status} />}>
            <p className="muted">
              <span className="badge prio-medium">{c.change_type}</span> {c.language} ·{" "}
              {c.rationale}
            </p>
            {c.diff ? <DiffView diff={c.diff} /> : <p className="muted">No diff.</p>}
          </SectionCard>
        ))
      )}
    </div>
  );
}
