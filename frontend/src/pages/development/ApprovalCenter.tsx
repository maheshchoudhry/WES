import { useState } from "react";
import { Link } from "react-router-dom";

import { developmentApi, type DevTask } from "../../api/development";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { useSession } from "../../auth/SessionContext";
import { useAsync } from "../../hooks/useAsync";

export function ApprovalCenter() {
  const { user } = useSession();
  const [busy, setBusy] = useState("");
  const { data, loading, error, reload } = useAsync<DevTask[]>(
    () => developmentApi.pendingApprovals().then((r) => r.data),
    [],
  );
  const canApprove = user?.role === "founder";

  async function decide(id: string, decision: string) {
    setBusy(id);
    try {
      await developmentApi.approve(id, decision, decision === "approved" ? "Approved" : "Rejected");
      reload();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy("");
    }
  }

  if (loading) return <Loading label="Loading approvals…" />;
  if (error) return <ErrorNotice message={error} />;
  const tasks = data ?? [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Approval Center</h1>
          <p>
            Pending pull requests awaiting the Founder&apos;s decision. Approval never auto-merges —
            a human performs the merge.
          </p>
        </div>
      </div>

      <SectionCard title={`Pending Approvals (${tasks.length})`}>
        {tasks.length === 0 ? (
          <Empty message="Nothing pending approval." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Title</th>
                  <th>Branch</th>
                  {canApprove && <th>Decision</th>}
                </tr>
              </thead>
              <tbody>
                {tasks.map((t) => (
                  <tr key={t.id}>
                    <td className="muted">{t.code}</td>
                    <td>
                      <Link to={`/development/tasks/${t.id}`}>{t.title}</Link>
                    </td>
                    <td className="muted">{t.branch_name}</td>
                    {canApprove && (
                      <td style={{ display: "flex", gap: 8 }}>
                        <button
                          className="btn btn-sm btn-primary"
                          disabled={busy === t.id}
                          onClick={() => decide(t.id, "approved")}
                        >
                          Approve
                        </button>
                        <button
                          className="btn btn-sm"
                          disabled={busy === t.id}
                          onClick={() => decide(t.id, "rejected")}
                        >
                          Reject
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
