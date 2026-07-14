import { useState } from "react";

import { repositoryApi, type RepoSymbol, symbolTypeLabel } from "../../api/repository";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { useAsync } from "../../hooks/useAsync";
import { useRepository } from "./useRepository";

const TYPES = [
  "",
  "class",
  "function",
  "method",
  "route",
  "model",
  "schema",
  "enum",
  "constant",
  "interface",
  "component",
  "type",
];

export function SymbolBrowser() {
  const { repo, loading: rl, error: re } = useRepository();
  const [type, setType] = useState("");
  const { data, loading, error } = useAsync<RepoSymbol[]>(
    async () => (repo ? (await repositoryApi.symbols(repo.id, type || undefined)).data : []),
    [repo?.id, type],
  );

  if (rl) return <Loading label="Loading repository…" />;
  if (re) return <ErrorNotice message={re} />;
  if (!repo) return <Empty message="No repository registered yet." />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Symbol Browser</h1>
          <p>Every class, function, route, and model in {repo.name}.</p>
        </div>
        <select aria-label="Symbol type" value={type} onChange={(e) => setType(e.target.value)}>
          {TYPES.map((t) => (
            <option key={t} value={t}>
              {t ? symbolTypeLabel(t) : "All types"}
            </option>
          ))}
        </select>
      </div>

      <SectionCard title={`Symbols (${data?.length ?? 0})`}>
        {loading ? (
          <Loading label="Loading symbols…" />
        ) : error ? (
          <ErrorNotice message={error} />
        ) : !data || data.length === 0 ? (
          <Empty message="No symbols match." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Parent</th>
                  <th>File</th>
                  <th>Line</th>
                </tr>
              </thead>
              <tbody>
                {data.map((s) => (
                  <tr key={s.id}>
                    <td>{s.name}</td>
                    <td>
                      <span className="badge prio-low">{symbolTypeLabel(s.symbol_type)}</span>
                    </td>
                    <td className="muted">{s.parent ?? "—"}</td>
                    <td className="muted">{s.file_path}</td>
                    <td>{s.line}</td>
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
