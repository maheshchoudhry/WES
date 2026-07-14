import { useState } from "react";

import { repositoryApi, type RepoFile, type RepoSymbol } from "../../api/repository";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { useAsync } from "../../hooks/useAsync";
import { useRepository } from "./useRepository";

const LAYERS = [
  "",
  "api",
  "service",
  "model",
  "schema",
  "repository",
  "utility",
  "configuration",
  "test",
  "migration",
  "documentation",
];

export function RepositoryExplorer() {
  const { repo, loading: rl, error: re } = useRepository();
  const [layer, setLayer] = useState("");
  const [selected, setSelected] = useState<RepoFile | null>(null);
  const [symbols, setSymbols] = useState<RepoSymbol[]>([]);

  const { data, loading, error } = useAsync<RepoFile[]>(
    async () => (repo ? (await repositoryApi.files(repo.id, layer || undefined)).data : []),
    [repo?.id, layer],
  );

  if (rl) return <Loading label="Loading repository…" />;
  if (re) return <ErrorNotice message={re} />;
  if (!repo) return <Empty message="No repository registered yet." />;

  async function open(f: RepoFile) {
    setSelected(f);
    const syms = await repositoryApi.fileSymbols(repo!.id, f.id);
    setSymbols(syms.data);
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Repository Explorer</h1>
          <p>Browse {repo.name} files by architecture layer; click a file to see its symbols.</p>
        </div>
        <select aria-label="Layer" value={layer} onChange={(e) => setLayer(e.target.value)}>
          {LAYERS.map((l) => (
            <option key={l} value={l}>
              {l || "All layers"}
            </option>
          ))}
        </select>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-col">
          <SectionCard title="Files">
            {loading ? (
              <Loading label="Loading files…" />
            ) : error ? (
              <ErrorNotice message={error} />
            ) : !data || data.length === 0 ? (
              <Empty message="No files in this layer." />
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Path</th>
                      <th>Lang</th>
                      <th>Layer</th>
                      <th>Symbols</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.map((f) => (
                      <tr key={f.id} style={{ cursor: "pointer" }} onClick={() => open(f)}>
                        <td>{f.path}</td>
                        <td className="muted">{f.language}</td>
                        <td>{f.layer}</td>
                        <td>{f.symbol_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </SectionCard>
        </div>
        <div className="dashboard-col">
          <SectionCard title={selected ? `Symbols — ${selected.name}` : "Symbols"}>
            {!selected ? (
              <p className="muted">Select a file to view its symbols.</p>
            ) : symbols.length === 0 ? (
              <Empty message="No symbols in this file." />
            ) : (
              <ul className="activity">
                {symbols.map((s) => (
                  <li key={s.id}>
                    <span className="activity-body">
                      <span className="activity-label">
                        {s.parent ? `${s.parent}.` : ""}
                        {s.name}
                      </span>
                      <span className="activity-time">{s.signature ?? `line ${s.line}`}</span>
                    </span>
                    <span className="badge prio-low">{s.symbol_type}</span>
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
