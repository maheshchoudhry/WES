import type { DataResponse, ListResponse } from "../types";
import { http } from "./client";

export interface RepoMetrics {
  file_count: number;
  module_count: number;
  symbol_count: number;
  class_count: number;
  function_count: number;
  route_count: number;
  model_count: number;
  line_count: number;
  dependency_count: number;
  test_file_count: number;
  technical_debt: number;
  health_score: number;
  languages: Record<string, number>;
}

export interface Repository {
  id: string;
  slug: string;
  name: string;
  root_path: string;
  description: string | null;
  primary_language: string | null;
  frameworks: string[];
  status: string;
  last_scanned_at: string | null;
  metrics: RepoMetrics | null;
}

export interface RepoFile {
  id: string;
  path: string;
  name: string;
  language: string;
  layer: string | null;
  line_count: number;
  symbol_count: number;
  is_test: boolean;
  is_config: boolean;
  is_generated: boolean;
}

export interface RepoSymbol {
  id: string;
  name: string;
  symbol_type: string;
  line: number;
  end_line: number | null;
  parent: string | null;
  signature: string | null;
  docstring: string | null;
  file_id: string;
  file_path: string | null;
}

export interface ArchLayer {
  layer: string;
  name: string;
  file_count: number;
  symbol_count: number;
  description: string | null;
}

export interface RepoModule {
  id: string;
  path: string;
  name: string;
  kind: string;
  file_count: number;
}

export interface SearchHit {
  term: string;
  kind: string;
  file_path: string | null;
  line: number | null;
  symbol_id: string | null;
  file_id: string | null;
}

export interface ImportGraph {
  nodes: { id: string; layer: string | null }[];
  edges: { source: string; target: string; external: boolean }[];
}

export interface ExternalDep {
  package: string;
  usages: number;
}

export interface Impact {
  file_path: string;
  dependencies: string[];
  dependents: string[];
  potential_breakages: string[];
  related_tests: string[];
  related_apis: { name: string; signature: string | null; line: number }[];
  related_documentation: string[];
}

export interface RepoDashboard extends Repository {
  architecture: ArchLayer[];
  external_dependencies: ExternalDep[];
  issues: { severity: string; category: string; message: string; file_path: string | null }[];
  todo_count: number;
}

export interface ScanResult {
  scan_id: string;
  status: string;
  file_count: number;
  symbol_count: number;
  module_count: number;
  duration_ms: number | null;
  summary: string | null;
  repository: Repository;
}

export const repositoryApi = {
  list: () => http.get<ListResponse<Repository>>("/repositories"),
  get: (id: string) => http.get<DataResponse<Repository>>(`/repositories/${id}`),
  register: (name: string, root_path: string, description?: string) =>
    http.post<DataResponse<Repository>>("/repositories", { name, root_path, description }),
  scan: (id: string) => http.post<DataResponse<ScanResult>>(`/repositories/${id}/scan`, {}),
  dashboard: (id: string) => http.get<DataResponse<RepoDashboard>>(`/repositories/${id}/dashboard`),
  files: (id: string, layer?: string) =>
    http.get<ListResponse<RepoFile>>(`/repositories/${id}/files${layer ? `?layer=${layer}` : ""}`),
  modules: (id: string) => http.get<ListResponse<RepoModule>>(`/repositories/${id}/modules`),
  architecture: (id: string) =>
    http.get<ListResponse<ArchLayer>>(`/repositories/${id}/architecture`),
  symbols: (id: string, symbolType?: string) =>
    http.get<ListResponse<RepoSymbol>>(
      `/repositories/${id}/symbols${symbolType ? `?symbol_type=${symbolType}` : ""}`,
    ),
  fileSymbols: (id: string, fileId: string) =>
    http.get<ListResponse<RepoSymbol>>(`/repositories/${id}/files/${fileId}/symbols`),
  references: (id: string, name: string) =>
    http.get<
      DataResponse<{
        definitions: RepoSymbol[];
        relationships: { source: string; target: string; type: string }[];
      }>
    >(`/repositories/${id}/references?name=${encodeURIComponent(name)}`),
  importGraph: (id: string) =>
    http.get<DataResponse<ImportGraph>>(`/repositories/${id}/import-graph`),
  dependencies: (id: string) =>
    http.get<ListResponse<ExternalDep>>(`/repositories/${id}/dependencies`),
  search: (id: string, q: string, kind?: string) =>
    http.get<ListResponse<SearchHit>>(
      `/repositories/${id}/search?q=${encodeURIComponent(q)}${kind ? `&kind=${kind}` : ""}`,
    ),
  impact: (id: string, filePath: string) =>
    http.get<DataResponse<Impact>>(
      `/repositories/${id}/impact?file_path=${encodeURIComponent(filePath)}`,
    ),
};

export const symbolTypeLabel = (t: string): string =>
  t.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
