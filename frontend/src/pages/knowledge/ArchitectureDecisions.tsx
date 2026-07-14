import { useState } from "react";

import { knowledgeApi, type ADR } from "../../api/knowledge";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useSession } from "../../auth/SessionContext";
import { useAsync } from "../../hooks/useAsync";

const CAN_WRITE = new Set(["founder", "director", "department_head"]);

export function ArchitectureDecisions() {
  const { user } = useSession();
  const [form, setForm] = useState({ title: "", context: "", decision: "", consequences: "" });
  const [busy, setBusy] = useState(false);
  const { data, loading, error, reload } = useAsync<ADR[]>(
    () => knowledgeApi.adrs().then((r) => r.data),
    [],
  );
  const canWrite = CAN_WRITE.has(user?.role ?? "");

  async function create() {
    if (form.title.length < 2) return;
    setBusy(true);
    try {
      await knowledgeApi.createAdr(form);
      setForm({ title: "", context: "", decision: "", consequences: "" });
      reload();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  async function accept(id: string) {
    await knowledgeApi.setAdrStatus(id, "accepted");
    reload();
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Architecture Decisions</h1>
          <p>Architecture Decision Records (ADRs) — durable decisions and their rationale.</p>
        </div>
      </div>

      {canWrite && (
        <SectionCard title="New ADR">
          <div style={{ display: "grid", gap: 8 }}>
            <input
              aria-label="ADR title"
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              placeholder="Decision title"
            />
            <input
              aria-label="Context"
              value={form.context}
              onChange={(e) => setForm((f) => ({ ...f, context: e.target.value }))}
              placeholder="Context — why this decision is needed"
            />
            <input
              aria-label="Decision"
              value={form.decision}
              onChange={(e) => setForm((f) => ({ ...f, decision: e.target.value }))}
              placeholder="Decision — what was decided"
            />
            <input
              aria-label="Consequences"
              value={form.consequences}
              onChange={(e) => setForm((f) => ({ ...f, consequences: e.target.value }))}
              placeholder="Consequences — trade-offs"
            />
            <div>
              <button
                className="btn btn-primary"
                disabled={busy || form.title.length < 2}
                onClick={create}
              >
                Create ADR
              </button>
            </div>
          </div>
        </SectionCard>
      )}

      <SectionCard title="Decision Records">
        {loading ? (
          <Loading label="Loading ADRs…" />
        ) : error ? (
          <ErrorNotice message={error} />
        ) : !data || data.length === 0 ? (
          <Empty message="No ADRs yet." />
        ) : (
          <div style={{ display: "grid", gap: 12 }}>
            {data.map((a) => (
              <div key={a.id} className="card">
                <div
                  style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}
                >
                  <h3 style={{ margin: 0 }}>
                    {a.code}: {a.title}
                  </h3>
                  <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    <StatusBadge status={a.status} />
                    {canWrite && a.status !== "accepted" && (
                      <button className="btn btn-sm" onClick={() => accept(a.id)}>
                        Accept
                      </button>
                    )}
                  </div>
                </div>
                {a.context && (
                  <p className="muted" style={{ margin: "8px 0 0" }}>
                    <strong>Context:</strong> {a.context}
                  </p>
                )}
                {a.decision && (
                  <p style={{ margin: "4px 0 0" }}>
                    <strong>Decision:</strong> {a.decision}
                  </p>
                )}
                {a.consequences && (
                  <p className="muted" style={{ margin: "4px 0 0" }}>
                    <strong>Consequences:</strong> {a.consequences}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}
