import type { DataResponse, ListResponse } from "../types";
import { http } from "./client";

export interface DevTask {
  id: string;
  code: string;
  title: string;
  description: string | null;
  status: string;
  branch_name: string | null;
  sandbox_path: string | null;
  repository_id: string | null;
  error: string | null;
  duration_ms: number | null;
  created_at: string | null;
  // present on detail
  plan?: DevPlan;
  changes?: DevChange[];
  tests?: DevTestRun[];
  review?: DevReview | null;
  pull_request?: DevPR | null;
  timeline?: DevStage[];
  metrics?: DevMetrics | null;
}

export interface DevPlan {
  summary: string;
  affected_files: string[];
  architecture_context: string;
  dependencies: string[];
  required_knowledge: string[];
  required_apis: string[];
  implementation_order: string[];
  risk_analysis: string;
  acceptance_criteria: string[];
}

export interface DevChange {
  id: string;
  path: string;
  change_type: string;
  language: string | null;
  content: string | null;
  diff: string | null;
  rationale: string | null;
  status: string;
}

export interface DevTestRun {
  kind: string;
  command: string | null;
  status: string;
  passed_count: number;
  failed_count: number;
  duration_ms: number | null;
}

export interface DevReviewComment {
  dimension: string;
  severity: string;
  file_path: string | null;
  message: string;
}

export interface DevReview {
  outcome: string;
  score: number;
  summary: string | null;
  comments: DevReviewComment[];
}

export interface DevPR {
  id: string;
  branch_name: string;
  base_branch: string;
  title: string;
  body: string | null;
  diff_summary: string | null;
  release_notes: string | null;
  status: string;
  commit_count: number;
  files_changed: number;
  additions: number;
  deletions: number;
}

export interface DevStage {
  stage: string;
  role: string | null;
  status: string;
  detail: string | null;
}

export interface DevMetrics {
  generated_files: number;
  files_changed: number;
  additions: number;
  deletions: number;
  commits: number;
  tests_run: number;
  tests_passed: number;
  review_score: number;
  duration_ms: number | null;
}

export interface DevFounderDash {
  running: number;
  completed: number;
  failed: number;
  pending_approvals: number;
  open_pull_requests: number;
  total_tasks: number;
  recent_tasks: DevTask[];
}

export const developmentApi = {
  tasks: (status?: string) =>
    http.get<ListResponse<DevTask>>(`/development/tasks${status ? `?status=${status}` : ""}`),
  task: (id: string) => http.get<DataResponse<DevTask>>(`/development/tasks/${id}`),
  createAndRun: (title: string, description?: string, provider_name?: string) =>
    http.post<DataResponse<DevTask>>("/development/run", { title, description, provider_name }),
  run: (id: string, provider_name?: string) =>
    http.post<DataResponse<DevTask>>(`/development/tasks/${id}/run`, { provider_name }),
  timeline: (id: string) => http.get<ListResponse<DevStage>>(`/development/tasks/${id}/timeline`),
  approve: (id: string, decision: string, notes?: string) =>
    http.post<DataResponse<DevTask>>(`/development/tasks/${id}/approve`, { decision, notes }),
  pendingApprovals: () => http.get<ListResponse<DevTask>>("/development/pending-approvals"),
  founderDashboard: () => http.get<DataResponse<DevFounderDash>>("/development/founder-dashboard"),
  team: () => http.get<ListResponse<AIAgent>>("/development/team"),
  orchestration: (id: string) =>
    http.get<DataResponse<Orchestration>>(`/development/tasks/${id}/orchestration`),
};

export interface AIAgent {
  employee: string;
  employee_code: string;
  role: string;
  authority: string;
  provider: string;
  responsibilities: string[];
  decision_rules: string[];
}

export interface Orchestration {
  stages: {
    stage: string;
    role: string | null;
    status: string;
    acting_employee: string | null;
    provider: string | null;
  }[];
  handoffs: {
    sequence: number;
    from_employee: string | null;
    to_employee: string | null;
    from_role: string | null;
    to_role: string | null;
    stage: string | null;
    summary: string | null;
  }[];
}

export const stageLabel = (s: string): string =>
  s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
