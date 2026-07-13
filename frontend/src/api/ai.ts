import type { DataResponse, ListResponse } from "../types";
import { http } from "./client";

export interface AICapabilityRef {
  code: string;
  name: string;
}

export interface AIKPI {
  name: string;
  target: string | null;
  unit: string | null;
}

export interface AIEmployee {
  id: string;
  employee_code: string;
  name: string;
  department_id: string;
  department_name: string | null;
  role_id: string;
  role_title: string | null;
  role_level: string | null;
  manager_id: string | null;
  manager_name: string | null;
  authority: string;
  decision_scope: string | null;
  status: string;
  version: number;
  responsibilities: string[];
  capabilities: AICapabilityRef[];
  kpis: AIKPI[];
  created_at: string;
  updated_at: string;
}

export interface AIDepartment {
  id: string;
  code: string;
  name: string;
  focus: string | null;
  status: string;
}

export interface AIRole {
  id: string;
  code: string;
  title: string;
  level: string;
  description: string | null;
  is_executive_head: boolean;
}

export interface AIOrgNode {
  id: string;
  employee_code: string;
  name: string;
  role_title: string | null;
  department_name: string | null;
  authority: string;
  status: string;
  reports: AIOrgNode[];
}

export interface AIDeptView {
  id: string;
  code: string;
  name: string;
  focus: string | null;
  employee_count: number;
  employees: {
    id: string;
    employee_code: string;
    name: string;
    role_title: string | null;
    authority: string;
    status: string;
  }[];
}

export interface AISummary {
  total_employees: number;
  department_count: number;
  role_count: number;
  by_status: Record<string, number>;
  by_department: Record<string, number>;
  ceo_present: boolean;
  organization_health: string;
}

export interface AIEmployeeInput {
  employee_code: string;
  name: string;
  department_id: string;
  role_id: string;
  manager_id?: string | null;
  authority?: string;
  decision_scope?: string | null;
  status?: string;
  responsibilities?: string[];
  capabilities?: string[];
  kpis?: AIKPI[];
}

export const aiApi = {
  listEmployees: (params: { departmentId?: string; search?: string } = {}) => {
    const q = new URLSearchParams();
    if (params.departmentId) q.set("department_id", params.departmentId);
    if (params.search) q.set("search", params.search);
    const qs = q.toString();
    return http.get<ListResponse<AIEmployee>>(`/ai-employees${qs ? `?${qs}` : ""}`);
  },
  getEmployee: (id: string) => http.get<DataResponse<AIEmployee>>(`/ai-employees/${id}`),
  createEmployee: (input: AIEmployeeInput) =>
    http.post<DataResponse<AIEmployee>>("/ai-employees", input),
  updateEmployee: (id: string, input: Partial<AIEmployeeInput>) =>
    http.patch<DataResponse<AIEmployee>>(`/ai-employees/${id}`, input),
  removeEmployee: (id: string) => http.del(`/ai-employees/${id}`),
  roles: () => http.get<ListResponse<AIRole>>("/ai-roles"),
  departments: () => http.get<ListResponse<AIDepartment>>("/ai-departments"),
  orgChart: () => http.get<DataResponse<AIOrgNode[]>>("/ai-org/chart"),
  departmentView: () => http.get<ListResponse<AIDeptView>>("/ai-org/departments"),
  summary: () => http.get<DataResponse<AISummary>>("/ai-org/summary"),
};
