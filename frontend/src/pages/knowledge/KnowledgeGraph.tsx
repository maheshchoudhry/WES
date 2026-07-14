import { Link } from "react-router-dom";

import { knowledgeApi, type GraphData, docTypeLabel } from "../../api/knowledge";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { useAsync } from "../../hooks/useAsync";

export function KnowledgeGraph() {
  const { data, loading, error } = useAsync<GraphData>(
    () => knowledgeApi.graph().then((r) => r.data),
    [],
  );
  if (loading) return <Loading label="Loading graph…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;

  const titleFor = (id: string) => data.nodes.find((n) => n.id === id)?.title ?? id.slice(0, 8);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Knowledge Graph</h1>
          <p>
            {data.nodes.length} documents · {data.edges.length} relationships. Every edge is
            queryable.
          </p>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-col">
          <SectionCard title="Documents (nodes)">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Title</th>
                    <th>Type</th>
                    <th>Links</th>
                  </tr>
                </thead>
                <tbody>
                  {data.nodes.map((n) => {
                    const links = data.edges.filter(
                      (e) => e.source === n.id || e.target === n.id,
                    ).length;
                    return (
                      <tr key={n.id}>
                        <td className="muted">{n.code}</td>
                        <td>
                          <Link to={`/knowledge/documents/${n.id}`}>{n.title}</Link>
                        </td>
                        <td className="muted">{docTypeLabel(n.doc_type)}</td>
                        <td>{links}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </SectionCard>
        </div>

        <div className="dashboard-col">
          <SectionCard title="Relationships (edges)">
            {data.edges.length === 0 ? (
              <Empty message="No relationships yet." />
            ) : (
              <ul className="activity">
                {data.edges.map((e) => (
                  <li key={e.id}>
                    <span className="activity-body">
                      <span className="activity-label">
                        {titleFor(e.source)} → {titleFor(e.target)}
                      </span>
                    </span>
                    <span className="badge prio-medium">{e.type}</span>
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
