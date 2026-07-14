import { executionApi, type Prompt } from "../../api/execution";
import { ErrorNotice, Loading } from "../../components/States";
import { useAsync } from "../../hooks/useAsync";

export function PromptLibrary() {
  const { data, loading, error } = useAsync<Prompt[]>(
    () => executionApi.prompts().then((r) => r.data),
    [],
  );
  if (loading) return <Loading label="Loading prompt library…" />;
  if (error) return <ErrorNotice message={error} />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Prompt Library</h1>
          <p>System, role, task, review, and escalation prompts for AI employees.</p>
        </div>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Code</th>
              <th>Name</th>
              <th>Type</th>
              <th>Version</th>
              <th>Content</th>
            </tr>
          </thead>
          <tbody>
            {(data ?? []).map((p) => (
              <tr key={p.id}>
                <td>{p.code}</td>
                <td>{p.name}</td>
                <td>
                  <span className="badge prio-medium">{p.prompt_type}</span>
                </td>
                <td>v{p.version}</td>
                <td className="muted">{p.content}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
