import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { knowledgeApi, type Category, DOC_TYPES, docTypeLabel } from "../../api/knowledge";
import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";

const EMPTY = {
  title: "",
  doc_type: "reference",
  summary: "",
  content: "",
  keywords: "",
  category_id: "",
  tags: "",
};

export function DocumentEditor() {
  const { id } = useParams();
  const editing = Boolean(id);
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [form, setForm] = useState(EMPTY);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const cats = await knowledgeApi.categories();
        if (active) setCategories(cats.data);
        if (editing && id) {
          const doc = (await knowledgeApi.document(id)).data;
          if (active)
            setForm({
              title: doc.title,
              doc_type: doc.doc_type,
              summary: doc.summary ?? "",
              content: doc.content ?? "",
              keywords: doc.keywords ?? "",
              category_id: doc.category_id ?? "",
              tags: doc.tags.join(", "),
            });
        }
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "Failed to load");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [id, editing]);

  const set =
    (k: keyof typeof form) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value }));

  async function save() {
    setBusy(true);
    try {
      const payload = {
        title: form.title,
        doc_type: form.doc_type,
        summary: form.summary || null,
        content: form.content,
        keywords: form.keywords || null,
        category_id: form.category_id || null,
        tags: form.tags
          ? form.tags
              .split(",")
              .map((t) => t.trim())
              .filter(Boolean)
          : [],
      };
      const result =
        editing && id
          ? await knowledgeApi.updateDocument(id, payload)
          : await knowledgeApi.createDocument(payload);
      navigate(`/knowledge/documents/${result.data.id}`);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Save failed");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Loading label="Loading editor…" />;
  if (error) return <ErrorNotice message={error} />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>{editing ? "Edit Document" : "New Document"}</h1>
          <p>Author organizational knowledge. Content changes are versioned.</p>
        </div>
      </div>

      <SectionCard title="Document">
        <div style={{ display: "grid", gap: 12 }}>
          <label>
            Title
            <input
              aria-label="Title"
              value={form.title}
              onChange={set("title")}
              placeholder="Document title"
            />
          </label>
          <label>
            Type
            <select aria-label="Type" value={form.doc_type} onChange={set("doc_type")}>
              {DOC_TYPES.map((t) => (
                <option key={t} value={t}>
                  {docTypeLabel(t)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Category
            <select aria-label="Category" value={form.category_id} onChange={set("category_id")}>
              <option value="">Uncategorized</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Summary
            <input
              aria-label="Summary"
              value={form.summary}
              onChange={set("summary")}
              placeholder="One-line summary"
            />
          </label>
          <label>
            Tags (comma-separated)
            <input
              aria-label="Tags"
              value={form.tags}
              onChange={set("tags")}
              placeholder="architecture, backend"
            />
          </label>
          <label>
            Keywords
            <input
              aria-label="Keywords"
              value={form.keywords}
              onChange={set("keywords")}
              placeholder="search keywords"
            />
          </label>
          <label>
            Content
            <textarea
              aria-label="Content"
              value={form.content}
              onChange={set("content")}
              rows={12}
              placeholder="Document body"
            />
          </label>
          <div>
            <button
              className="btn btn-primary"
              disabled={busy || form.title.length < 2}
              onClick={save}
            >
              {busy ? "Saving…" : editing ? "Save Changes" : "Create Document"}
            </button>
          </div>
        </div>
      </SectionCard>
    </div>
  );
}
