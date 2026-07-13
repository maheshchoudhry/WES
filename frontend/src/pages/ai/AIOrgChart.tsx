import { aiApi, type AIOrgNode } from "../../api/ai";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { useAsync } from "../../hooks/useAsync";

function Node({ node }: { node: AIOrgNode }) {
  return (
    <li>
      <div className="org-node">
        <span className="org-name">{node.name}</span>
        <span className="muted org-role">
          {node.role_title} · {node.department_name}
        </span>
      </div>
      {node.reports.length > 0 && (
        <ul>
          {node.reports.map((child) => (
            <Node key={child.id} node={child} />
          ))}
        </ul>
      )}
    </li>
  );
}

export function AIOrgChart() {
  const { data, loading, error } = useAsync<AIOrgNode[]>(
    () => aiApi.orgChart().then((r) => r.data),
    [],
  );

  if (loading) return <Loading label="Loading organization chart…" />;
  if (error) return <ErrorNotice message={error} />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>AI Organization Chart</h1>
          <p>Reporting hierarchy of the AI company.</p>
        </div>
      </div>
      <div className="card">
        {!data || data.length === 0 ? (
          <Empty message="No AI employees to display." />
        ) : (
          <ul className="org-tree">
            {data.map((root) => (
              <Node key={root.id} node={root} />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
