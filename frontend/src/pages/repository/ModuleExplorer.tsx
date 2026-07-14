import { repositoryApi, type RepoModule } from "../../api/repository";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { useAsync } from "../../hooks/useAsync";
import { useRepository } from "./useRepository";

export function ModuleExplorer() {
  const { repo, loading: rl, error: re } = useRepository();
  const { data, loading, error } = useAsync<RepoModule[]>(
    async () => (repo ? (await repositoryApi.modules(repo.id)).data : []),
    [repo?.id],
  );

  if (rl || loading) return <Loading label="Loading modules…" />;
  if (re || error) return <ErrorNotice message={re || error || ""} />;
  if (!repo) return <Empty message="No repository registered yet." />;
  const modules = data ?? [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Module Explorer</h1>
          <p>Modules (directories/packages) in {repo.name}, by file count.</p>
        </div>
      </div>

      <SectionCard title={`Modules (${modules.length})`}>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Path</th>
                <th>Kind</th>
                <th>Files</th>
              </tr>
            </thead>
            <tbody>
              {modules.map((m) => (
                <tr key={m.id}>
                  <td>{m.path}</td>
                  <td>
                    <span className="badge prio-low">{m.kind}</span>
                  </td>
                  <td>{m.file_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>
    </div>
  );
}
