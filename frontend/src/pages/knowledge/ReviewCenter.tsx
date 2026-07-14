import { useState } from "react";
import { Link } from "react-router-dom";

import { knowledgeApi, type KnowledgeDoc, docTypeLabel } from "../../api/knowledge";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useSession } from "../../auth/SessionContext";
import { useAsync } from "../../hooks/useAsync";

const CAN_APPROVE = new Set(["founder", "director"]);

export function ReviewCenter() {
  const { user } = useSession();
  const [busy, setBusy] = useState(false);
  const { data, loading, error, reload } = useAsync<KnowledgeDoc[]>(
    () => knowledgeApi.pendingReviews().then((r) => r.data),
    [],
  );
  const canApprove = CAN_APPROVE.has(user?.role ?? "");

  async function decide(id: string, decision: string) {
    setBusy(true);
    try {
      await knowledgeApi.review(
        id,
        decision,
        decision === "approved" ? "Approved" : "Please revise",
      );
      reload();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Review Center</h1>
          <p>
            Documents awaiting approval. {canApprove ? "Approve or request changes." : "Read-only."}
          </p>
        </div>
      </div>

      <SectionCard title="Pending Reviews">
        {loading ? (
          <Loading label="Loading reviews…" />
        ) : error ? (
          <ErrorNotice message={error} />
        ) : !data || data.length === 0 ? (
          <Empty message="Nothing pending review." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Title</th>
                  <th>Type</th>
                  <th>Status</th>
                  {canApprove && <th>Actions</th>}
                </tr>
              </thead>
              <tbody>
                {data.map((d) => (
                  <tr key={d.id}>
                    <td className="muted">{d.code}</td>
                    <td>
                      <Link to={`/knowledge/documents/${d.id}`}>{d.title}</Link>
                    </td>
                    <td className="muted">{docTypeLabel(d.doc_type)}</td>
                    <td>
                      <StatusBadge status={d.status} />
                    </td>
                    {canApprove && (
                      <td style={{ display: "flex", gap: 8 }}>
                        <button
                          className="btn btn-sm btn-primary"
                          disabled={busy}
                          onClick={() => decide(d.id, "approved")}
                        >
                          Approve
                        </button>
                        <button
                          className="btn btn-sm"
                          disabled={busy}
                          onClick={() => decide(d.id, "changes_requested")}
                        >
                          Changes
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>
    </div>
  );
}
