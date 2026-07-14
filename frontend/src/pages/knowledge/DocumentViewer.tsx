import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  knowledgeApi,
  type DocVersion,
  type KnowledgeDoc,
  type Review,
  docTypeLabel,
} from "../../api/knowledge";
import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useSession } from "../../auth/SessionContext";
import { useAsync } from "../../hooks/useAsync";

interface Data {
  doc: KnowledgeDoc;
  versions: DocVersion[];
  related: KnowledgeDoc[];
  reviews: Review[];
}

const CAN_APPROVE = new Set(["founder", "director"]);
const CAN_WRITE = new Set(["founder", "director", "department_head"]);

export function DocumentViewer() {
  const { id = "" } = useParams();
  const { user } = useSession();
  const [busy, setBusy] = useState(false);

  const { data, loading, error, reload } = useAsync<Data>(async () => {
    const [doc, versions, related, reviews] = await Promise.all([
      knowledgeApi.document(id),
      knowledgeApi.versions(id),
      knowledgeApi.related(id),
      knowledgeApi.reviews(id),
    ]);
    return { doc: doc.data, versions: versions.data, related: related.data, reviews: reviews.data };
  }, [id]);

  if (loading) return <Loading label="Loading document…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;
  const { doc } = data;
  const role = user?.role ?? "";

  async function act(fn: () => Promise<unknown>) {
    setBusy(true);
    try {
      await fn();
      reload();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>{doc.title}</h1>
          <p>
            {doc.code} · {docTypeLabel(doc.doc_type)} · {doc.category_name ?? "Uncategorized"} · v
            {doc.version}
          </p>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <StatusBadge status={doc.status} />
          <button
            className="btn btn-sm"
            disabled={busy}
            onClick={() => act(() => knowledgeApi.addBookmark(doc.id))}
          >
            Bookmark
          </button>
          {CAN_WRITE.has(role) && (
            <Link to={`/knowledge/documents/${doc.id}/edit`} className="btn btn-sm">
              Edit
            </Link>
          )}
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-col">
          <SectionCard title="Content">
            {doc.summary && <p className="muted">{doc.summary}</p>}
            <div className="chat-content" style={{ whiteSpace: "pre-wrap" }}>
              {doc.content}
            </div>
            {doc.tags.length > 0 && (
              <div className="quick-actions" style={{ marginTop: 12 }}>
                {doc.tags.map((t) => (
                  <span key={t} className="badge prio-low">
                    {t}
                  </span>
                ))}
              </div>
            )}
          </SectionCard>

          <SectionCard title="Knowledge Graph">
            <h4>Relationships</h4>
            {doc.relationships && doc.relationships.length > 0 ? (
              <ul className="activity">
                {doc.relationships.map((r) => (
                  <li key={r.id}>
                    <span className="activity-body">
                      <span className="activity-label">
                        {r.source_title} → {r.target_title}
                      </span>
                    </span>
                    <span className="badge prio-medium">{r.relationship_type}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted">No relationships.</p>
            )}
            <h4>References</h4>
            {doc.references && doc.references.length > 0 ? (
              <ul className="activity">
                {doc.references.map((r) => (
                  <li key={r.id}>
                    <span className="activity-body">
                      <span className="activity-label">{r.label ?? r.entity_type}</span>
                    </span>
                    <span className="badge prio-low">{r.entity_type}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted">No references.</p>
            )}
          </SectionCard>
        </div>

        <div className="dashboard-col">
          <SectionCard title="Review">
            {doc.status !== "approved" && CAN_WRITE.has(role) && (
              <button
                className="btn btn-sm"
                disabled={busy}
                onClick={() => act(() => knowledgeApi.submit(doc.id))}
              >
                Submit for Review
              </button>
            )}
            {CAN_APPROVE.has(role) && (
              <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                <button
                  className="btn btn-sm btn-primary"
                  disabled={busy}
                  onClick={() => act(() => knowledgeApi.review(doc.id, "approved", "Approved"))}
                >
                  Approve
                </button>
                <button
                  className="btn btn-sm"
                  disabled={busy}
                  onClick={() =>
                    act(() => knowledgeApi.review(doc.id, "changes_requested", "Please revise"))
                  }
                >
                  Request Changes
                </button>
              </div>
            )}
            {data.reviews.length > 0 ? (
              <ul className="activity" style={{ marginTop: 12 }}>
                {data.reviews.map((r) => (
                  <li key={r.id}>
                    <span className="activity-body">
                      <span className="activity-label">{r.reviewer_name}</span>
                      <span className="activity-time">{r.comment}</span>
                    </span>
                    <StatusBadge status={r.decision} />
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted" style={{ marginTop: 12 }}>
                No reviews yet.
              </p>
            )}
          </SectionCard>

          <SectionCard title="Version History">
            <ul className="activity">
              {data.versions.map((v) => (
                <li key={v.id}>
                  <span className="activity-body">
                    <span className="activity-label">v{v.version}</span>
                    <span className="activity-time">{v.change_summary}</span>
                  </span>
                  {CAN_WRITE.has(role) && v.version !== doc.version && (
                    <button
                      className="btn btn-sm"
                      disabled={busy}
                      onClick={() => act(() => knowledgeApi.restore(doc.id, v.version))}
                    >
                      Restore
                    </button>
                  )}
                </li>
              ))}
            </ul>
          </SectionCard>

          <SectionCard title="Related Documents">
            {data.related.length === 0 ? (
              <p className="muted">None.</p>
            ) : (
              <ul className="activity">
                {data.related.map((r) => (
                  <li key={r.id}>
                    <span className="activity-body">
                      <Link to={`/knowledge/documents/${r.id}`} className="activity-label">
                        {r.title}
                      </Link>
                    </span>
                    <span className="badge prio-low">{docTypeLabel(r.doc_type)}</span>
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
