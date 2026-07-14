import { useState } from "react";

import { knowledgeApi, type Collection } from "../../api/knowledge";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { useSession } from "../../auth/SessionContext";
import { useAsync } from "../../hooks/useAsync";

const CAN_WRITE = new Set(["founder", "director", "department_head"]);

export function Collections() {
  const { user } = useSession();
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const { data, loading, error, reload } = useAsync<Collection[]>(
    () => knowledgeApi.collections().then((r) => r.data),
    [],
  );
  const canWrite = CAN_WRITE.has(user?.role ?? "");

  async function create() {
    if (name.length < 2) return;
    setBusy(true);
    try {
      await knowledgeApi.createCollection(name);
      setName("");
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
          <h1>Collections</h1>
          <p>Curated sets of documents for a topic or workflow.</p>
        </div>
      </div>

      {canWrite && (
        <div
          className="card"
          style={{ display: "flex", gap: 12, marginBottom: 16, alignItems: "center" }}
        >
          <input
            aria-label="Collection name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="New collection name"
          />
          <button className="btn btn-primary" disabled={busy || name.length < 2} onClick={create}>
            Create Collection
          </button>
        </div>
      )}

      {loading ? (
        <Loading label="Loading collections…" />
      ) : error ? (
        <ErrorNotice message={error} />
      ) : !data || data.length === 0 ? (
        <Empty message="No collections yet." />
      ) : (
        <div className="grid dept-grid">
          {data.map((c) => (
            <SectionCard key={c.id} title={c.name}>
              <p className="muted">{c.description}</p>
              <span className="badge prio-medium">{c.document_count} documents</span>
            </SectionCard>
          ))}
        </div>
      )}
    </div>
  );
}
