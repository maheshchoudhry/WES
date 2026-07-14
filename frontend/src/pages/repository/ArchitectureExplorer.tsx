import { repositoryApi, type ArchLayer } from "../../api/repository";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { useAsync } from "../../hooks/useAsync";
import { useRepository } from "./useRepository";

export function ArchitectureExplorer() {
  const { repo, loading: rl, error: re } = useRepository();
  const { data, loading, error } = useAsync<ArchLayer[]>(
    async () => (repo ? (await repositoryApi.architecture(repo.id)).data : []),
    [repo?.id],
  );

  if (rl || loading) return <Loading label="Loading architecture…" />;
  if (re || error) return <ErrorNotice message={re || error || ""} />;
  if (!repo) return <Empty message="No repository registered yet." />;
  const layers = data ?? [];
  const total = layers.reduce((n, l) => n + l.file_count, 0);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Architecture Explorer</h1>
          <p>Detected layers in {repo.name} — automatically classified from paths and content.</p>
        </div>
      </div>

      <div className="grid dept-grid">
        {layers.map((l) => (
          <SectionCard key={l.layer} title={l.name}>
            <div className="grid stats">
              <StatCard label="Files" value={l.file_count} />
              <StatCard label="Symbols" value={l.symbol_count} />
              <StatCard
                label="Share"
                value={total ? `${Math.round((l.file_count / total) * 100)}%` : "0%"}
              />
            </div>
            <p className="muted" style={{ marginTop: 8 }}>
              {l.description}
            </p>
          </SectionCard>
        ))}
      </div>
    </div>
  );
}
