import { useState } from "react";
import { Link } from "react-router-dom";

import {
  knowledgeApi,
  type Category,
  type KnowledgeDoc,
  DOC_TYPES,
  docTypeLabel,
} from "../../api/knowledge";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

interface Data {
  documents: KnowledgeDoc[];
  categories: Category[];
}

export function KnowledgeLibrary() {
  const [category, setCategory] = useState("");
  const [docType, setDocType] = useState("");
  const [status, setStatus] = useState("");

  const { data, loading, error } = useAsync<Data>(async () => {
    const [documents, categories] = await Promise.all([
      knowledgeApi.documents({
        category_id: category || undefined,
        doc_type: docType || undefined,
        status: status || undefined,
      }),
      knowledgeApi.categories(),
    ]);
    return { documents: documents.data, categories: categories.data };
  }, [category, docType, status]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Knowledge Library</h1>
          <p>Browse and filter every organizational document.</p>
        </div>
        <Link to="/knowledge/new" className="btn btn-primary">
          New Document
        </Link>
      </div>

      <div
        className="card"
        style={{
          display: "flex",
          gap: 12,
          marginBottom: 16,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <select
          aria-label="Category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="">All categories</option>
          {(data?.categories ?? []).map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <select aria-label="Type" value={docType} onChange={(e) => setDocType(e.target.value)}>
          <option value="">All types</option>
          {DOC_TYPES.map((t) => (
            <option key={t} value={t}>
              {docTypeLabel(t)}
            </option>
          ))}
        </select>
        <select aria-label="Status" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          <option value="draft">Draft</option>
          <option value="in_review">In Review</option>
          <option value="approved">Approved</option>
          <option value="archived">Archived</option>
          <option value="deprecated">Deprecated</option>
        </select>
        <Link to="/knowledge/search" className="btn btn-sm">
          Advanced Search
        </Link>
      </div>

      {loading ? (
        <Loading label="Loading documents…" />
      ) : error ? (
        <ErrorNotice message={error} />
      ) : !data || data.documents.length === 0 ? (
        <Empty message="No documents match these filters." />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Title</th>
                <th>Type</th>
                <th>Category</th>
                <th>Status</th>
                <th>Version</th>
                <th>Tags</th>
              </tr>
            </thead>
            <tbody>
              {data.documents.map((d) => (
                <tr key={d.id}>
                  <td className="muted">{d.code}</td>
                  <td>
                    <Link to={`/knowledge/documents/${d.id}`}>{d.title}</Link>
                  </td>
                  <td className="muted">{docTypeLabel(d.doc_type)}</td>
                  <td>{d.category_name ?? "—"}</td>
                  <td>
                    <StatusBadge status={d.status} />
                  </td>
                  <td>v{d.version}</td>
                  <td className="muted">{d.tags.join(", ") || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
