import { Link } from "react-router-dom";

import { knowledgeApi, type Category } from "../../api/knowledge";
import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { useAsync } from "../../hooks/useAsync";

export function CategoryExplorer() {
  const { data, loading, error } = useAsync<Category[]>(
    () => knowledgeApi.categories().then((r) => r.data),
    [],
  );
  if (loading) return <Loading label="Loading categories…" />;
  if (error) return <ErrorNotice message={error} />;
  const categories = data ?? [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Category Explorer</h1>
          <p>The knowledge taxonomy — {categories.length} categories.</p>
        </div>
      </div>

      <SectionCard title="Categories">
        <div className="grid dept-grid">
          {categories.map((c) => (
            <Link
              key={c.id}
              to={`/knowledge/library`}
              className="card"
              style={{ textDecoration: "none" }}
            >
              <h3 style={{ margin: 0 }}>{c.name}</h3>
              <p className="muted" style={{ margin: "6px 0" }}>
                {c.description}
              </p>
              <span className="badge prio-medium">{c.document_count ?? 0} documents</span>
            </Link>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}
