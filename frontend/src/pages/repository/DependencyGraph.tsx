import { repositoryApi, type ExternalDep, type ImportGraph } from "../../api/repository";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { useAsync } from "../../hooks/useAsync";
import { useRepository } from "./useRepository";

export function DependencyGraph() {
  const { repo, loading: rl, error: re } = useRepository();
  const { data, loading, error } = useAsync<{
    graph: ImportGraph;
    deps: ExternalDep[];
  }>(async () => {
    if (!repo) return { graph: { nodes: [], edges: [] }, deps: [] };
    const [graph, deps] = await Promise.all([
      repositoryApi.importGraph(repo.id),
      repositoryApi.dependencies(repo.id),
    ]);
    return { graph: graph.data, deps: deps.data };
  }, [repo?.id]);

  if (rl || loading) return <Loading label="Loading dependency graph…" />;
  if (re || error) return <ErrorNotice message={re || error || ""} />;
  if (!repo || !data) return <Empty message="No repository registered yet." />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Dependency Graph</h1>
          <p>
            Internal import graph — {data.graph.nodes.length} files, {data.graph.edges.length}{" "}
            edges.
          </p>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-col">
          <SectionCard title="Internal Imports (edges)">
            {data.graph.edges.length === 0 ? (
              <Empty message="No internal imports found." />
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Source</th>
                      <th>Imports</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.graph.edges.slice(0, 200).map((e, i) => (
                      <tr key={i}>
                        <td>{e.source}</td>
                        <td className="muted">{e.target}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </SectionCard>
        </div>
        <div className="dashboard-col">
          <SectionCard title="External Packages">
            <ul className="activity">
              {data.deps.map((d) => (
                <li key={d.package}>
                  <span className="activity-body">
                    <span className="activity-label">{d.package}</span>
                  </span>
                  <span className="badge prio-low">{d.usages}×</span>
                </li>
              ))}
            </ul>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
