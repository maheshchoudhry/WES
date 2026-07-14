import { executionApi, type ReviewItem } from "../../api/execution";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

export function ReviewQueue() {
  const { data, loading, error, reload } = useAsync<ReviewItem[]>(
    () => executionApi.reviews().then((r) => r.data),
    [],
  );
  if (loading) return <Loading label="Loading review queue…" />;
  if (error) return <ErrorNotice message={error} />;
  const items = data ?? [];

  async function decide(item: ReviewItem, status: string) {
    try {
      await executionApi.decideReview(item.id, status);
      reload();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Decision failed");
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Review Queue</h1>
          <p>Work submitted for review by AI reviewers.</p>
        </div>
      </div>
      {items.length === 0 ? (
        <Empty message="Nothing to review." />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Task</th>
                <th>Reviewer</th>
                <th>Submitter</th>
                <th>Status</th>
                <th>Notes</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {items.map((r) => (
                <tr key={r.id}>
                  <td>{r.work_item_code ?? "—"}</td>
                  <td>{r.reviewer_name}</td>
                  <td>{r.submitter_name ?? "—"}</td>
                  <td>
                    <StatusBadge status={r.status} />
                  </td>
                  <td className="muted">{r.notes ?? "—"}</td>
                  <td>
                    {r.status === "pending" && (
                      <div className="row-actions">
                        <button className="btn btn-sm" onClick={() => decide(r, "approved")}>
                          Approve
                        </button>
                        <button
                          className="btn btn-sm btn-danger"
                          onClick={() => decide(r, "changes_requested")}
                        >
                          Changes
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
