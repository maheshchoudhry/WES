import { Link } from "react-router-dom";

import { repositoryApi, type RepoDashboard, type Repository } from "../../api/repository";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { useAsync } from "../../hooks/useAsync";

export function RepositoryDashboard() {
  const { data, loading, error, reload } = useAsync<{
    repo: Repository | null;
    dash: RepoDashboard | null;
  }>(async () => {
    const repos = await repositoryApi.list();
    const repo = repos.data[0] ?? null;
    const dash = repo ? (await repositoryApi.dashboard(repo.id)).data : null;
    return { repo, dash };
  }, []);
  if (loading) return <Loading label="Loading repository…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data?.repo || !data.dash) return <Empty message="No repository registered yet." />;

  const d = data.dash;
  const m = d.metrics;

  async function rescan() {
    if (data?.repo) {
      await repositoryApi.scan(data.repo.id);
      reload();
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Repository Intelligence</h1>
          <p>
            {d.name} · {d.primary_language ?? "—"} ·{" "}
            {d.frameworks.length ? d.frameworks.join(", ") : "no frameworks detected"}
          </p>
        </div>
        <button className="btn btn-primary" onClick={rescan}>
          Re-scan
        </button>
      </div>

      {m && (
        <>
          <div className="grid stats span-all">
            <StatCard label="Files" value={m.file_count} />
            <StatCard label="Symbols" value={m.symbol_count} />
            <StatCard label="Lines" value={m.line_count} />
            <StatCard
              label="Health"
              value={m.health_score.toFixed(0)}
              accent={m.health_score >= 60 ? "ok" : "warn"}
              hint="/ 100"
            />
          </div>
          <div className="grid stats span-all" style={{ marginTop: 12 }}>
            <StatCard label="Classes" value={m.class_count} />
            <StatCard label="Functions" value={m.function_count} />
            <StatCard label="Routes" value={m.route_count} />
            <StatCard label="Models" value={m.model_count} />
          </div>
          <div className="grid stats span-all" style={{ marginTop: 12 }}>
            <StatCard label="Modules" value={m.module_count} />
            <StatCard label="Dependencies" value={m.dependency_count} />
            <StatCard label="Test Files" value={m.test_file_count} />
            <StatCard
              label="Technical Debt"
              value={m.technical_debt}
              accent={m.technical_debt > 0 ? "warn" : "ok"}
              hint={`${d.todo_count} TODOs`}
            />
          </div>
        </>
      )}

      <SectionCard
        title="Architecture"
        action={
          <Link to="/repository/architecture" className="btn btn-sm">
            Explore
          </Link>
        }
      >
        <div className="quick-actions">
          {d.architecture.map((a) => (
            <span key={a.layer} className="badge prio-medium">
              {a.name}: {a.file_count} files
            </span>
          ))}
        </div>
      </SectionCard>

      <div className="dashboard-grid">
        <div className="dashboard-col">
          <SectionCard title="Top External Dependencies">
            {d.external_dependencies.length === 0 ? (
              <p className="muted">None detected.</p>
            ) : (
              <ul className="activity">
                {d.external_dependencies.map((dep) => (
                  <li key={dep.package}>
                    <span className="activity-body">
                      <span className="activity-label">{dep.package}</span>
                    </span>
                    <span className="badge prio-low">{dep.usages}×</span>
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
        </div>
        <div className="dashboard-col">
          <SectionCard title="Issues & Technical Debt">
            {d.issues.length === 0 ? (
              <p className="muted">No issues detected.</p>
            ) : (
              <ul className="activity">
                {d.issues.map((i, idx) => (
                  <li key={idx}>
                    <span className="activity-body">
                      <span className="activity-label">{i.message}</span>
                      <span className="activity-time">{i.file_path}</span>
                    </span>
                    <span className="badge prio-medium">{i.severity}</span>
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
        </div>
      </div>

      <SectionCard title="Languages">
        <div className="quick-actions">
          {m &&
            Object.entries(m.languages).map(([lang, count]) => (
              <span key={lang} className="badge prio-low">
                {lang}: {count}
              </span>
            ))}
        </div>
      </SectionCard>
    </div>
  );
}
