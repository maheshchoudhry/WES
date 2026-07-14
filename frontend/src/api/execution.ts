import type { DataResponse, ListResponse } from "../types";
import { http } from "./client";

export interface Prompt {
  id: string;
  code: string;
  name: string;
  prompt_type: string;
  content: string;
  version: number;
  author: string | null;
}

export interface SOP {
  id: string;
  code: string;
  title: string;
  category: string;
  content: string;
  version: number;
}

export interface DecisionRule {
  id: string;
  ai_role_id: string;
  rule_type: string;
  name: string;
  description: string | null;
  authority_limit: string | null;
}

export interface QueueItem {
  id: string;
  ai_employee_id: string;
  ai_employee_name: string | null;
  work_item_id: string | null;
  work_item_code: string | null;
  title: string;
  description: string | null;
  priority: string;
  status: string;
  position: number;
  started_at: string | null;
  completed_at: string | null;
}

export interface HistoryEntry {
  id: string;
  ai_employee_id: string;
  ai_employee_name: string | null;
  work_item_id: string | null;
  action: string;
  output: string | null;
  status: string;
  duration_seconds: number | null;
  created_at: string;
}

export interface ReviewItem {
  id: string;
  work_item_id: string | null;
  work_item_code: string | null;
  reviewer_ai_employee_id: string;
  reviewer_name: string | null;
  submitter_ai_employee_id: string | null;
  submitter_name: string | null;
  status: string;
  notes: string | null;
  reviewed_at: string | null;
  created_at: string;
}

export interface Handoff {
  id: string;
  work_item_id: string | null;
  work_item_code: string | null;
  from_ai_employee_id: string | null;
  from_name: string | null;
  to_ai_employee_id: string;
  to_name: string | null;
  stage: string;
  status: string;
  notes: string | null;
  sequence: number;
}

export interface Workspace {
  employee: {
    id: string;
    employee_code: string;
    name: string;
    role: string | null;
    department: string | null;
  };
  context: string | null;
  inbox: Handoff[];
  assigned_tasks: {
    id: string;
    task_code: string;
    title: string;
    status: string;
    priority: string;
  }[];
  queue: QueueItem[];
  review_queue: ReviewItem[];
  history: HistoryEntry[];
  context_items: { key: string; value: string }[];
  kpis: { name: string; target: string | null; unit: string | null }[];
  performance: {
    queued: number;
    in_progress: number;
    completed: number;
    pending_reviews: number;
    avg_duration_seconds: number | null;
  };
}

export interface ExecFounderDash {
  ai_work_queue: number;
  queued: number;
  in_progress: number;
  pending_reviews: number;
  completed_work: number;
  avg_completion_seconds: number | null;
  organization_performance: { total_executions: number; handoffs: number };
}

export interface ExecAIDash {
  inbox: number;
  current_work: number;
  execution_queue: number;
  review_queue: number;
  history: number;
  work_by_employee: Record<string, number>;
}

export const executionApi = {
  prompts: () => http.get<ListResponse<Prompt>>("/prompts"),
  sops: () => http.get<ListResponse<SOP>>("/sops"),
  decisionRules: () => http.get<ListResponse<DecisionRule>>("/decision-rules"),
  workspace: (employeeId: string) => http.get<DataResponse<Workspace>>(`/workspaces/${employeeId}`),
  queue: (params: { aiEmployeeId?: string; status?: string } = {}) => {
    const q = new URLSearchParams();
    if (params.aiEmployeeId) q.set("ai_employee_id", params.aiEmployeeId);
    if (params.status) q.set("status", params.status);
    const qs = q.toString();
    return http.get<ListResponse<QueueItem>>(`/execution-queue${qs ? `?${qs}` : ""}`);
  },
  advanceQueue: (id: string, status: string, output?: string) =>
    http.post<DataResponse<QueueItem>>(`/execution-queue/${id}/advance`, { status, output }),
  history: () => http.get<ListResponse<HistoryEntry>>("/execution-history"),
  reviews: (status?: string) =>
    http.get<ListResponse<ReviewItem>>(`/reviews${status ? `?status=${status}` : ""}`),
  decideReview: (id: string, status: string, notes?: string) =>
    http.post<DataResponse<ReviewItem>>(`/reviews/${id}/decision`, { status, notes }),
  handoffs: (workItemId?: string) =>
    http.get<ListResponse<Handoff>>(`/handoffs${workItemId ? `?work_item_id=${workItemId}` : ""}`),
  founderDashboard: () => http.get<DataResponse<ExecFounderDash>>("/execution/founder-dashboard"),
  aiDashboard: () => http.get<DataResponse<ExecAIDash>>("/execution/ai-dashboard"),
};
