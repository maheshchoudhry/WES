import { Link } from "react-router-dom";

import { knowledgeApi, type Bookmark } from "../../api/knowledge";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { useAsync } from "../../hooks/useAsync";

export function Bookmarks() {
  const { data, loading, error, reload } = useAsync<Bookmark[]>(
    () => knowledgeApi.bookmarks().then((r) => r.data),
    [],
  );

  async function remove(documentId: string) {
    await knowledgeApi.removeBookmark(documentId);
    reload();
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Bookmarks</h1>
          <p>Your saved documents for quick access.</p>
        </div>
      </div>

      <SectionCard title="Saved Documents">
        {loading ? (
          <Loading label="Loading bookmarks…" />
        ) : error ? (
          <ErrorNotice message={error} />
        ) : !data || data.length === 0 ? (
          <Empty message="No bookmarks yet. Bookmark a document from its page." />
        ) : (
          <ul className="activity">
            {data.map((b) => (
              <li key={b.id}>
                <span className="activity-body">
                  <Link to={`/knowledge/documents/${b.document_id}`} className="activity-label">
                    {b.document_title}
                  </Link>
                  <span className="activity-time">{b.document_code}</span>
                </span>
                <button className="btn btn-sm" onClick={() => remove(b.document_id)}>
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
      </SectionCard>
    </div>
  );
}
