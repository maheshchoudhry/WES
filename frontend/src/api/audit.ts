import type { ListResponse } from "../types";
import { http } from "./client";

export interface AuditEntry {
  id: string;
  action: string;
  actor: string | null;
  category: string;
  entity_type: string | null;
  entity_id: string | null;
  ip: string | null;
  severity: string;
  detail: string | null;
  created_at: string | null;
}

export const auditApi = {
  list: (category?: string) =>
    http.get<ListResponse<AuditEntry>>(`/audit${category ? `?category=${category}` : ""}`),
};
