import type { DataResponse, ListResponse } from "../types";
import { http } from "./client";

export interface Provider {
  id: string;
  name: string;
  display_name: string;
  enabled: boolean;
  is_default: boolean;
  default_model: string | null;
  config: Record<string, string | null>;
  health: string;
}

export interface Run {
  id: string;
  thread_id: string | null;
  ai_employee_id: string | null;
  ai_employee_name: string | null;
  provider_id: string;
  provider_name: string | null;
  model: string | null;
  prompt_version: string | null;
  status: string;
  input_summary: string | null;
  output: string | null;
  error: string | null;
  review_outcome: string | null;
  review_notes: string | null;
  duration_ms: number | null;
  created_at: string | null;
}

export interface OrchMessage {
  id: string;
  role: string;
  content: string;
  sequence: number;
}

export interface OrchFounderDash {
  providers: { name: string; enabled: boolean; is_default: boolean; health: string }[];
  running_executions: number;
  failed_executions: number;
  completed_executions: number;
  execution_queue: number;
  token_usage: number;
  estimated_cost: number;
  avg_runtime_ms: number | null;
}

export const orchestrationApi = {
  providers: () => http.get<ListResponse<Provider>>("/providers"),
  roleMappings: () => http.get<DataResponse<Record<string, string>>>("/providers/role-mappings"),
  healthCheck: () => http.post<DataResponse<unknown>>("/providers/health-check", {}),
  setEnabled: (id: string, enabled: boolean) =>
    http.patch<DataResponse<Provider>>(`/providers/${id}/enabled`, { enabled }),
  setDefault: (id: string) => http.post<DataResponse<Provider>>(`/providers/${id}/default`, {}),
  setConfig: (id: string, key: string, value: string) =>
    http.post<DataResponse<Provider>>(`/providers/${id}/config`, { key, value }),
  mapRole: (roleCode: string, providerName: string) =>
    http.post<DataResponse<Record<string, string>>>("/providers/role-mappings", {
      role_code: roleCode,
      provider_name: providerName,
    }),
  runs: (status?: string) =>
    http.get<ListResponse<Run>>(`/orchestration/runs${status ? `?status=${status}` : ""}`),
  run: (input: { ai_employee_id: string; work_item_id?: string; provider_name?: string }) =>
    http.post<DataResponse<Run>>("/orchestration/run", input),
  review: (id: string, outcome: string, notes?: string) =>
    http.post<DataResponse<Run>>(`/orchestration/runs/${id}/review`, { outcome, notes }),
  threadMessages: (threadId: string) =>
    http.get<ListResponse<OrchMessage>>(`/orchestration/threads/${threadId}/messages`),
  founderDashboard: () =>
    http.get<DataResponse<OrchFounderDash>>("/orchestration/founder-dashboard"),
};
