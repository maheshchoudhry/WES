import type { DataResponse, ListResponse } from "../types";
import { http } from "./client";

export interface KnowledgeDoc {
  id: string;
  code: string;
  slug: string;
  title: string;
  doc_type: string;
  category_id: string | null;
  category_name: string | null;
  summary: string | null;
  status: string;
  version: number;
  tags: string[];
  is_pinned: boolean;
  view_count: number;
  author_id: string | null;
  approver_id: string | null;
  updated_at: string | null;
  created_at: string | null;
  // present on the detail endpoint
  content?: string;
  keywords?: string | null;
  relationships?: Relationship[];
  references?: Reference[];
}

export interface Category {
  id: string;
  code: string;
  name: string;
  description: string | null;
  parent_id: string | null;
  position: number;
  document_count: number | null;
}

export interface Relationship {
  id: string;
  source_document_id: string;
  source_title: string | null;
  target_document_id: string;
  target_title: string | null;
  relationship_type: string;
  note: string | null;
}

export interface Reference {
  id: string;
  document_id: string;
  entity_type: string;
  entity_id: string | null;
  label: string | null;
}

export interface DocVersion {
  id: string;
  document_id: string;
  version: number;
  title: string;
  change_summary: string | null;
  status: string;
  created_at: string | null;
}

export interface Review {
  id: string;
  document_id: string;
  reviewer_name: string | null;
  decision: string;
  comment: string | null;
  reviewed_at: string | null;
}

export interface Collection {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  owner_id: string | null;
  document_count: number;
  documents?: { document_id: string; title: string | null; position: number }[];
}

export interface Bookmark {
  id: string;
  document_id: string;
  document_title: string | null;
  document_code: string | null;
  note: string | null;
  created_at: string | null;
}

export interface ADR {
  id: string;
  code: string;
  title: string;
  status: string;
  context: string | null;
  decision: string | null;
  consequences: string | null;
  document_id: string | null;
  decided_at: string | null;
  created_at: string | null;
}

export interface GraphData {
  nodes: {
    id: string;
    code: string;
    title: string;
    doc_type: string;
    category_id: string | null;
  }[];
  edges: { id: string; source: string; target: string; type: string }[];
}

export interface DocBrief {
  id: string;
  code: string;
  title: string;
  doc_type: string;
  summary: string | null;
}

export interface RetrievalBundle {
  relevant_documents: DocBrief[];
  relevant_sop: DocBrief[];
  relevant_adr: DocBrief[];
  relevant_standards: DocBrief[];
  relevant_decisions: DocBrief[];
  relevant_templates: DocBrief[];
  relevant_references: { document_id: string; entity_type: string; label: string | null }[];
}

export interface KnowledgeFounderDash {
  documents: number;
  categories: number;
  pending_reviews: number;
  approved_documents: number;
  knowledge_health: string;
  approved_coverage: number;
  recent_knowledge: KnowledgeDoc[];
  most_used: KnowledgeDoc[];
  statistics: {
    total_documents: number;
    total_categories: number;
    total_adrs: number;
    total_views: number;
    retrievals: number;
    by_status: Record<string, number>;
    by_type: Record<string, number>;
  };
}

export interface KnowledgeAIDash {
  suggested_knowledge: DocBrief[];
  recent_knowledge: KnowledgeDoc[];
  architecture_references: DocBrief[];
  coding_standards: DocBrief[];
  sop_recommendations: DocBrief[];
  organization_memory: DocBrief[];
  related_documents: DocBrief[];
}

export interface DocumentInput {
  title: string;
  doc_type: string;
  content?: string;
  summary?: string | null;
  category_id?: string | null;
  keywords?: string | null;
  tags?: string[];
}

const qs = (params: Record<string, string | undefined>): string => {
  const entries = Object.entries(params).filter(([, v]) => v);
  return entries.length
    ? `?${entries.map(([k, v]) => `${k}=${encodeURIComponent(v as string)}`).join("&")}`
    : "";
};

export const knowledgeApi = {
  // documents
  documents: (filters: { category_id?: string; doc_type?: string; status?: string } = {}) =>
    http.get<ListResponse<KnowledgeDoc>>(`/knowledge/documents${qs(filters)}`),
  document: (id: string) => http.get<DataResponse<KnowledgeDoc>>(`/knowledge/documents/${id}`),
  createDocument: (input: DocumentInput) =>
    http.post<DataResponse<KnowledgeDoc>>("/knowledge/documents", input),
  updateDocument: (id: string, input: Partial<DocumentInput> & { change_summary?: string }) =>
    http.patch<DataResponse<KnowledgeDoc>>(`/knowledge/documents/${id}`, input),
  versions: (id: string) =>
    http.get<ListResponse<DocVersion>>(`/knowledge/documents/${id}/versions`),
  restore: (id: string, version: number) =>
    http.post<DataResponse<KnowledgeDoc>>(
      `/knowledge/documents/${id}/versions/${version}/restore`,
      {},
    ),
  related: (id: string) =>
    http.get<ListResponse<KnowledgeDoc>>(`/knowledge/documents/${id}/related`),
  submit: (id: string) =>
    http.post<DataResponse<KnowledgeDoc>>(`/knowledge/documents/${id}/submit`, {}),
  reviews: (id: string) => http.get<ListResponse<Review>>(`/knowledge/documents/${id}/reviews`),
  review: (id: string, decision: string, comment?: string) =>
    http.post<DataResponse<Review>>(`/knowledge/documents/${id}/review`, { decision, comment }),
  addReference: (id: string, entity_type: string, label?: string) =>
    http.post<DataResponse<Reference>>(`/knowledge/documents/${id}/references`, {
      entity_type,
      label,
    }),
  // categories / tags
  categories: () => http.get<ListResponse<Category>>("/knowledge/categories"),
  // search / retrieval
  search: (filters: {
    q?: string;
    category_id?: string;
    doc_type?: string;
    tag?: string;
    status?: string;
  }) => http.get<ListResponse<KnowledgeDoc>>(`/knowledge/search${qs(filters)}`),
  retrieve: (keywords?: string) =>
    http.get<DataResponse<RetrievalBundle>>(`/knowledge/retrieve${qs({ keywords })}`),
  // graph
  graph: () => http.get<DataResponse<GraphData>>("/knowledge/graph"),
  createRelationship: (source: string, target: string, type: string, note?: string) =>
    http.post<DataResponse<Relationship>>("/knowledge/relationships", {
      source_document_id: source,
      target_document_id: target,
      relationship_type: type,
      note,
    }),
  // dashboards
  founderDashboard: () =>
    http.get<DataResponse<KnowledgeFounderDash>>("/knowledge/founder-dashboard"),
  aiDashboard: (keywords?: string) =>
    http.get<DataResponse<KnowledgeAIDash>>(`/knowledge/ai-dashboard${qs({ keywords })}`),
  // reviews
  pendingReviews: () => http.get<ListResponse<KnowledgeDoc>>("/knowledge/reviews/pending"),
  // adrs
  adrs: () => http.get<ListResponse<ADR>>("/knowledge/adrs"),
  createAdr: (input: {
    title: string;
    context?: string;
    decision?: string;
    consequences?: string;
  }) => http.post<DataResponse<ADR>>("/knowledge/adrs", input),
  setAdrStatus: (id: string, status: string) =>
    http.patch<DataResponse<ADR>>(`/knowledge/adrs/${id}/status`, { status }),
  // bookmarks
  bookmarks: () => http.get<ListResponse<Bookmark>>("/knowledge/bookmarks"),
  addBookmark: (document_id: string, note?: string) =>
    http.post<DataResponse<Bookmark>>("/knowledge/bookmarks", { document_id, note }),
  removeBookmark: (document_id: string) => http.del(`/knowledge/bookmarks/${document_id}`),
  // collections
  collections: () => http.get<ListResponse<Collection>>("/knowledge/collections"),
  collection: (id: string) => http.get<DataResponse<Collection>>(`/knowledge/collections/${id}`),
  createCollection: (name: string, description?: string) =>
    http.post<DataResponse<Collection>>("/knowledge/collections", { name, description }),
  addToCollection: (collectionId: string, document_id: string) =>
    http.post<DataResponse<Collection>>(`/knowledge/collections/${collectionId}/documents`, {
      document_id,
    }),
};

export const DOC_TYPES = [
  "architecture",
  "adr",
  "sop",
  "specification",
  "api",
  "design",
  "meeting_notes",
  "research",
  "reference",
  "coding_standard",
  "security_standard",
  "deployment_guide",
  "troubleshooting_guide",
  "project_documentation",
  "lessons_learned",
  "policy",
  "template",
];

export const docTypeLabel = (t: string): string =>
  t.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
