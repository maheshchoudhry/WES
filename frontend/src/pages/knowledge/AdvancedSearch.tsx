import { useState } from "react";
import { Link } from "react-router-dom";

import {
  knowledgeApi,
  type Category,
  type KnowledgeDoc,
  DOC_TYPES,
  docTypeLabel,
} from "../../api/knowledge";
import { Empty, ErrorNotice } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

export function AdvancedSearch() {
  const [q, setQ] = useState("");
  const [docType, setDocType] = useState("");
  const [tag, setTag] = useState("");
  const [results, setResults] = useState<KnowledgeDoc[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);

  const { data: categories } = useAsync<Category[]>(
    () => knowledgeApi.categories().then((r) => r.data),
    [],
  );
  const [category, setCategory] = useState("");

  async function run() {
    setSearching(true);
    setError(null);
    try {
      const resp = await knowledgeApi.search({
        q: q || undefined,
        category_id: category || undefined,
        doc_type: docType || undefined,
        tag: tag || undefined,
      });
      setResults(resp.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setSearching(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Advanced Search</h1>
          <p>Keyword + full-text search across the knowledge base, with filters.</p>
        </div>
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
        <input
          aria-label="Query"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && run()}
          placeholder="Search title, summary, content, keywords…"
          style={{ flex: 1, minWidth: 220 }}
        />
        <select
          aria-label="Category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="">All categories</option>
          {(categories ?? []).map((c) => (
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
        <input
          aria-label="Tag"
          value={tag}
          onChange={(e) => setTag(e.target.value)}
          placeholder="tag"
        />
        <button className="btn btn-primary" disabled={searching} onClick={run}>
          {searching ? "Searching…" : "Search"}
        </button>
      </div>

      {error && <ErrorNotice message={error} />}

      <SectionCard title={results ? `Results (${results.length})` : "Results"}>
        {!results ? (
          <p className="muted">Enter a query and search.</p>
        ) : results.length === 0 ? (
          <Empty message="No documents matched." />
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
                </tr>
              </thead>
              <tbody>
                {results.map((d) => (
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
