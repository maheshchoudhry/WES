import type { DataResponse, ListResponse } from "../types";
import { http } from "./client";

export interface PipelineStage {
  stage: string;
  status: string;
  detail: string | null;
}

export interface Pipeline {
  id: string;
  code: string;
  task_id: string | null;
  status: string;
  environment_target: string;
  current_stage: string | null;
  triggered_by: string | null;
  duration_ms: number | null;
  error: string | null;
  created_at: string | null;
  stages: PipelineStage[];
  release?: ReleaseVersion | null;
  deployments?: Deployment[];
  build?: {
    status: string;
    language: string | null;
    checksum: string | null;
    output: string | null;
    duration_ms: number | null;
  } | null;
}

export interface ReleaseVersion {
  id: string;
  version: string;
  status: string;
  channel: string;
  created_by: string | null;
  created_at: string | null;
  notes: {
    title: string;
    summary: string | null;
    changes: string[];
    highlights: string | null;
  } | null;
  deployments: { environment: string; status: string }[];
}

export interface Deployment {
  id: string;
  environment: string;
  status: string;
  strategy: string;
  version: string | null;
  path: string | null;
  approved_by: string | null;
  detail: string | null;
  duration_ms: number | null;
  created_at: string | null;
}

export interface EnvironmentProfile {
  id: string;
  name: string;
  display_name: string;
  requires_approval: boolean;
  strategy: string;
  variables: Record<string, string>;
  active: boolean;
}

export interface SystemHealthSnapshot {
  overall_status: string;
  app_status: string;
  api_status: string;
  db_status: string;
  provider_status: string;
  cpu_pct: number;
  memory_pct: number;
  disk_pct: number;
  queue_depth: number;
  response_time_ms: number;
  created_at: string | null;
}

export interface MonitoringEvent {
  category: string;
  metric: string;
  value: number;
  unit: string | null;
  status: string;
  detail: string | null;
  created_at: string | null;
}

export interface Incident {
  id: string;
  code: string;
  title: string;
  severity: string;
  status: string;
  source: string;
  detail: string | null;
  recovery_action: string | null;
  created_at: string | null;
}

export interface RollbackEntry {
  id: string;
  environment: string;
  status: string;
  from_version: string | null;
  to_version: string | null;
  reason: string | null;
  actor: string | null;
  created_at: string | null;
}

export interface DevOpsFounderDash {
  total_pipelines: number;
  running: number;
  awaiting_production: number;
  passed: number;
  failed: number;
  deployments: number;
  production_deployments: number;
  releases: number;
  open_incidents: number;
  system_health: SystemHealthSnapshot | null;
  recent_pipelines: Pipeline[];
}

export const devopsApi = {
  pipelines: (status?: string) =>
    http.get<ListResponse<Pipeline>>(`/devops/pipelines${status ? `?status=${status}` : ""}`),
  pipeline: (id: string) => http.get<DataResponse<Pipeline>>(`/devops/pipelines/${id}`),
  runPipeline: (task_id: string, environment = "staging") =>
    http.post<DataResponse<Pipeline>>("/devops/pipelines/run", { task_id, environment }),
  deployProduction: (id: string) =>
    http.post<DataResponse<Pipeline>>(`/devops/pipelines/${id}/deploy-production`, {}),
  deployments: (environment?: string) =>
    http.get<ListResponse<Deployment>>(
      `/devops/deployments${environment ? `?environment=${environment}` : ""}`,
    ),
  releases: () => http.get<ListResponse<ReleaseVersion>>("/devops/releases"),
  environments: () => http.get<ListResponse<EnvironmentProfile>>("/devops/environments"),
  rollback: (environment: string, to_release_id: string, reason?: string) =>
    http.post<DataResponse<{ status: string }>>("/devops/rollback", {
      environment,
      to_release_id,
      reason,
    }),
  rollbackHistory: () => http.get<ListResponse<RollbackEntry>>("/devops/rollback-history"),
  snapshot: () => http.post<DataResponse<SystemHealthSnapshot>>("/devops/monitoring/snapshot", {}),
  health: () => http.get<DataResponse<SystemHealthSnapshot | null>>("/devops/monitoring/health"),
  events: () => http.get<ListResponse<MonitoringEvent>>("/devops/monitoring/events"),
  incidents: (status?: string) =>
    http.get<ListResponse<Incident>>(`/devops/incidents${status ? `?status=${status}` : ""}`),
  resolveIncident: (id: string) =>
    http.post<DataResponse<Incident>>(`/devops/incidents/${id}/resolve`, {}),
  founderDashboard: () => http.get<DataResponse<DevOpsFounderDash>>("/devops/founder-dashboard"),
};

export const stageLabel = (s: string): string =>
  s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
