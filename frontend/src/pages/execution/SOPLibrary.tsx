import { executionApi, type SOP } from "../../api/execution";
import { ErrorNotice, Loading } from "../../components/States";
import { useAsync } from "../../hooks/useAsync";

export function SOPLibrary() {
  const { data, loading, error } = useAsync<SOP[]>(
    () => executionApi.sops().then((r) => r.data),
    [],
  );
  if (loading) return <Loading label="Loading SOP library…" />;
  if (error) return <ErrorNotice message={error} />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>SOP Library</h1>
          <p>Standard operating procedures: coding, review, testing, deployment, docs, security.</p>
        </div>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Code</th>
              <th>Title</th>
              <th>Category</th>
              <th>Version</th>
              <th>Content</th>
            </tr>
          </thead>
          <tbody>
            {(data ?? []).map((s) => (
              <tr key={s.id}>
                <td>{s.code}</td>
                <td>{s.title}</td>
                <td>
                  <span className="badge prio-low">{s.category}</span>
                </td>
                <td>v{s.version}</td>
                <td className="muted">{s.content}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
