import type { DataResponse, ListResponse } from "../types";
import { http } from "./client";

export interface GateCheck {
  code: string;
  name: string;
  value?: number;
  threshold?: number;
  passed: boolean;
  skipped?: boolean;
}

export interface QualityGate {
  id: string;
  task_id: string;
  status: string;
  architecture_score: number;
  code_score: number;
  security_score: number;
  performance_score: number;
  documentation_score: number;
  overall_score: number;
  tests_passed_pct: number;
  formatting_clean: boolean;
  lint_clean: boolean;
  documentation_complete: boolean;
  critical_count: number;
  high_count: number;
  total_findings: number;
  approval_eligible: boolean;
  gates: GateCheck[];
  summary: string | null;
}

export interface Finding {
  engine?: string | null;
  category: string;
  severity: string;
  file_path?: string | null;
  line?: number | null;
  package?: string | null;
  cwe?: string | null;
  message: string;
}

export interface QualityMetrics {
  risk_score: number;
  impact_score: number;
  confidence_score: number;
  complexity_score: number;
  maintainability_score: number;
}

export interface ReleaseReadiness {
  status: string;
  ready: boolean;
  score: number;
  blockers: string[];
  summary: string | null;
}

export interface QualityReport {
  gate: QualityGate | null;
  review_findings: Finding[];
  security_findings: Finding[];
  performance_findings: Finding[];
  dependency_findings: Finding[];
  documentation_findings: Finding[];
  compliance: { policy: string; status: string; message: string }[];
  metrics: QualityMetrics | null;
  release_readiness: ReleaseReadiness | null;
}

export interface QualityRule {
  code: string;
  name: string;
  category: string;
  operator: string;
  threshold: number;
  severity: string;
  enabled: boolean;
  mandatory: boolean;
  description: string | null;
}

export interface QualityFounderDash {
  total_gate_runs: number;
  approval_eligible: number;
  blocked: number;
  avg_review_score: number;
  avg_security_score: number;
  avg_performance_score: number;
  open_critical: number;
  release_ready: number;
  recent: {
    task_id: string;
    overall_score: number;
    security_score: number;
    approval_eligible: boolean;
    critical_count: number;
  }[];
}

export const qualityApi = {
  rules: () => http.get<ListResponse<QualityRule>>("/quality/rules"),
  gate: (taskId: string) =>
    http.get<DataResponse<QualityGate | null>>(`/quality/tasks/${taskId}/gate`),
  report: (taskId: string) =>
    http.get<DataResponse<QualityReport>>(`/quality/tasks/${taskId}/report`),
  evaluate: (taskId: string) =>
    http.post<DataResponse<QualityGate>>(`/quality/tasks/${taskId}/evaluate`, {}),
  founderDashboard: () => http.get<DataResponse<QualityFounderDash>>("/quality/founder-dashboard"),
};

export const SEVERITY_BADGE: Record<string, string> = {
  critical: "prio-critical",
  high: "prio-high",
  medium: "prio-medium",
  low: "prio-low",
  info: "prio-low",
};
