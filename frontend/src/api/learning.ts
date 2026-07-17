import type { DataResponse, ListResponse } from "../types";
import { http } from "./client";

export interface LearningRule {
  id: string;
  kind: string;
  rule: string;
  dimension: string | null;
  occurrences: number;
  applied_count: number;
  evidence: string | null;
  active: boolean;
}

export interface LearningSummary {
  total_rules: number;
  total_applications: number;
  by_kind: Record<string, number>;
}

export const learningApi = {
  rules: (kind?: string) =>
    http.get<ListResponse<LearningRule>>(`/learning/rules${kind ? `?kind=${kind}` : ""}`),
  summary: () => http.get<DataResponse<LearningSummary>>("/learning/summary"),
};
