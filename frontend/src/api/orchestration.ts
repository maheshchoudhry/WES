import type { DataResponse, ListResponse } from "../types";
import { http } from "./client";

export interface ProviderModel {
  id: string;
  code: string;
  display_name: string;
  is_default: boolean;
  enabled: boolean;
  context_window: number | null;
  input_cost_per_1k: number;
  output_cost_per_1k: number;
}

export interface Provider {
  id: string;
  name: string;
  display_name: string;
  enabled: boolean;
  is_default: boolean;
  default_model: string | null;
  active_model: string | null;
  priority: number;
  config: Record<string, string | null>;
  has_secret: boolean;
  secret_hint: string | null;
  models: ProviderModel[];
  health: string;
  health_detail: string | null;
}

export interface ConnectionResult {
  provider: string;
  ok: boolean;
  status: string;
  detail: string | null;
  model?: string;
  version?: string;
  latency_ms?: number;
}

export interface ProviderMetric {
  provider: string;
  avg_latency_ms: number | null;
  errors: number;
  tokens: number;
  cost: number;
}

export interface ProviderEventItem {
  id: string;
  provider: string | null;
  event_type: string;
  actor: string | null;
  detail: string | null;
  severity: string;
  created_at: string | null;
}

export interface CostRow {
  key: string | null;
  label: string;
  tokens: number;
  cost: number;
}

export interface BudgetStatus {
  config: {
    daily_cost_limit: number | null;
    monthly_cost_limit: number | null;
    max_cost: number | null;
    max_tokens: number | null;
    warning_threshold: number;
    hard_stop: boolean;
    currency: string;
  };
  daily_spent: number;
  monthly_spent: number;
  daily_pct: number;
  monthly_pct: number;
  warning: boolean;
  exceeded: boolean;
  hard_stop_active: boolean;
}

export interface PlatformDash {
  providers: {
    name: string;
    enabled: boolean;
    is_default: boolean;
    health: string;
    active_model: string | null;
    has_secret: boolean;
    priority: number;
  }[];
  running_executions: number;
  failed_executions: number;
  completed_executions: number;
  token_usage: number;
  estimated_cost: number;
  avg_latency_ms: number | null;
  budget: BudgetStatus;
  metrics: ProviderMetric[];
  recent_events: ProviderEventItem[];
  cost_by_provider: CostRow[];
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

  // -- Live provider platform (Sprint 11) --
  setSecret: (id: string, value: string) =>
    http.post<DataResponse<Provider>>(`/providers/${id}/secret`, { value }),
  testConnection: (id: string) =>
    http.post<DataResponse<ConnectionResult>>(`/providers/${id}/test`, {}),
  models: (id: string) => http.get<ListResponse<ProviderModel>>(`/providers/${id}/models`),
  addModel: (id: string, code: string, display_name: string) =>
    http.post<DataResponse<ProviderModel>>(`/providers/${id}/models`, { code, display_name }),
  setActiveModel: (id: string, model_code: string) =>
    http.post<DataResponse<Provider>>(`/providers/${id}/active-model`, { model_code }),
  setPriority: (id: string, priority: number) =>
    http.post<DataResponse<Provider>>(`/providers/${id}/priority`, { priority }),
  platformDashboard: () => http.get<DataResponse<PlatformDash>>("/providers/dashboard"),
  metrics: () => http.get<ListResponse<ProviderMetric>>("/providers/metrics"),
  events: () => http.get<ListResponse<ProviderEventItem>>("/providers/events"),
  cost: (groupBy: string) => http.get<ListResponse<CostRow>>(`/providers/cost?group_by=${groupBy}`),
  budget: () => http.get<DataResponse<BudgetStatus>>("/providers/budget"),
  updateBudget: (config: Partial<BudgetStatus["config"]>) =>
    http.put<DataResponse<BudgetStatus>>("/providers/budget", config),
  monitor: () => http.post<ListResponse<ConnectionResult>>("/providers/monitor", {}),
  cancelRun: (runId: string) =>
    http.post<DataResponse<{ cancelled: boolean }>>(`/orchestration/runs/${runId}/cancel`, {}),
};

// Server-Sent-Events streaming: yields (eventType, data) via a callback.
export async function streamExecution(
  body: { ai_employee_id: string; work_item_id?: string; provider_name?: string },
  onEvent: (type: string, data: Record<string, unknown>) => void,
): Promise<void> {
  const { tokenStore } = await import("../auth/tokenStore");
  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  const resp = await fetch(`${base}/api/v1/orchestration/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(tokenStore.access ? { Authorization: `Bearer ${tokenStore.access}` } : {}),
    },
    body: JSON.stringify(body),
  });
  if (!resp.ok || !resp.body) throw new Error(`Stream failed (${resp.status})`);
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      let type = "message";
      let data = "";
      for (const line of frame.split("\n")) {
        if (line.startsWith("event:")) type = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (data) {
        try {
          onEvent(type, JSON.parse(data));
        } catch {
          /* ignore malformed frame */
        }
      }
    }
  }
}
