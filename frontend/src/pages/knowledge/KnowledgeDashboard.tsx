import { Link } from "react-router-dom";

import { knowledgeApi, type KnowledgeFounderDash, docTypeLabel } from "../../api/knowledge";
import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

export function KnowledgeDashboard() {
  const { data, loading, error } = useAsync<KnowledgeFounderDash>(
    () => knowledgeApi.founderDashboard().then((r) => r.data),
    [],
  );
  if (loading) return <Loading label="Loading knowledge…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;

  const healthAccent: "ok" | "warn" | "muted" =
    data.knowledge_health === "healthy"
      ? "ok"
      : data.knowledge_health === "empty"
        ? "muted"
        : "warn";

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Knowledge Dashboard</h1>
          <p>The single source of truth for WES. Every AI execution retrieves from here.</p>
        </div>
        <Link to="/knowledge/library" className="btn btn-primary">
          Open Library
        </Link>
      </div>

      <div className="grid stats span-all">
        <StatCard label="Documents" value={data.documents} />
        <StatCard label="Categories" value={data.categories} />
        <StatCard label="Approved" value={data.approved_documents} accent="ok" />
        <StatCard
          label="Pending Reviews"
          value={data.pending_reviews}
          accent={data.pending_reviews > 0 ? "warn" : "ok"}
        />
      </div>

      <div className="grid stats span-all" style={{ marginTop: 12 }}>
        <StatCard label="ADRs" value={data.statistics.total_adrs} />
        <StatCard label="Total Views" value={data.statistics.total_views} />
        <StatCard label="AI Retrievals" value={data.statistics.retrievals} />
        <StatCard
          label="Knowledge Health"
          value={<span style={{ textTransform: "capitalize" }}>{data.knowledge_health}</span>}
          accent={healthAccent}
          hint={`${Math.round(data.approved_coverage * 100)}% approved`}
        />
      </div>

      <SectionCard title="Recent Knowledge">
        {data.recent_knowledge.length === 0 ? (
          <p className="muted">No documents yet.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Title</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Views</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_knowledge.map((d) => (
                  <tr key={d.id}>
                    <td className="muted">{d.code}</td>
                    <td>
                      <Link to={`/knowledge/documents/${d.id}`}>{d.title}</Link>
                    </td>
                    <td className="muted">{docTypeLabel(d.doc_type)}</td>
                    <td>
                      <StatusBadge status={d.status} />
                    </td>
                    <td>{d.view_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>

      <SectionCard title="Most Used Documents">
        <ul className="activity">
          {data.most_used.map((d) => (
            <li key={d.id}>
              <span className="activity-body">
                <Link to={`/knowledge/documents/${d.id}`} className="activity-label">
                  {d.title}
                </Link>
              </span>
              <span className="badge prio-medium">{d.view_count} views</span>
            </li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard title="Documents by Type">
        <div className="quick-actions">
          {Object.entries(data.statistics.by_type).map(([type, count]) => (
            <span key={type} className="badge prio-low">
              {docTypeLabel(type)}: {count}
            </span>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}
