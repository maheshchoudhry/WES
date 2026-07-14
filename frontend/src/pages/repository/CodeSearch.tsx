import { useState } from "react";

import { repositoryApi, type SearchHit, symbolTypeLabel } from "../../api/repository";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { useRepository } from "./useRepository";

const KINDS = [
  "",
  "file",
  "class",
  "function",
  "method",
  "route",
  "model",
  "component",
  "interface",
];

export function CodeSearch() {
  const { repo, loading, error } = useRepository();
  const [q, setQ] = useState("");
  const [kind, setKind] = useState("");
  const [results, setResults] = useState<SearchHit[] | null>(null);
  const [busy, setBusy] = useState(false);

  if (loading) return <Loading label="Loading repository…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!repo) return <Empty message="No repository registered yet." />;

  async function run() {
    setBusy(true);
    try {
      const res = await repositoryApi.search(repo!.id, q, kind || undefined);
      setResults(res.data);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Code Search</h1>
          <p>Search files, classes, functions, routes, and models across {repo.name}.</p>
        </div>
      </div>

      <div
        className="card"
        style={{
          display: "flex",
          gap: 12,
          marginBottom: 16,
          alignItems: "center",
          flexWrap: "wrap",
        }}
      >
        <input
          aria-label="Query"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && run()}
          placeholder="Search symbols and files…"
          style={{ flex: 1, minWidth: 220 }}
        />
        <select aria-label="Kind" value={kind} onChange={(e) => setKind(e.target.value)}>
          {KINDS.map((k) => (
            <option key={k} value={k}>
              {k ? symbolTypeLabel(k) : "All kinds"}
            </option>
          ))}
        </select>
        <button className="btn btn-primary" onClick={run} disabled={busy}>
          {busy ? "Searching…" : "Search"}
        </button>
      </div>

      <SectionCard title={results ? `Results (${results.length})` : "Results"}>
        {!results ? (
          <p className="muted">Enter a query and search.</p>
        ) : results.length === 0 ? (
          <Empty message="No matches." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Kind</th>
                  <th>File</th>
                  <th>Line</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r, i) => (
                  <tr key={i}>
                    <td>{r.term}</td>
                    <td>
                      <span className="badge prio-low">{symbolTypeLabel(r.kind)}</span>
                    </td>
                    <td className="muted">{r.file_path}</td>
                    <td>{r.line ?? "—"}</td>
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
