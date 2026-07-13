import type { DataResponse, ListResponse } from "../types";
import { http } from "./client";

export interface CompanySummary {
  id: string;
  name: string;
  slug: string;
  company_type: string;
  purpose: string | null;
  status: string;
  department_count: number;
  employee_count: number;
}

export interface DashboardStats {
  company: CompanySummary | null;
  totals: { departments: number; employees: number; active_projects: number };
  employees_by_status: Record<string, number>;
  employees_by_authority: Record<string, number>;
  departments_by_status: Record<string, number>;
}

export interface DepartmentStat {
  id: string;
  code: string;
  name: string;
  focus: string | null;
  status: string;
  employee_count: number;
}

export interface EmployeeDirectoryItem {
  id: string;
  employee_code: string;
  full_name: string;
  position: string;
  authority: string;
  status: string;
  department_id: string | null;
  department_name: string | null;
  reports_to_id: string | null;
  manager_name: string | null;
}

export interface ActivityItem {
  entity_type: "company" | "department" | "employee";
  action: "created" | "updated";
  entity_id: string;
  label: string;
  timestamp: string;
}

export interface SystemHealth {
  api: string;
  database: string;
  version: string;
  companies: number;
  departments: number;
  employees: number;
}

export const dashboardApi = {
  companySummary: () => http.get<DataResponse<CompanySummary | null>>("/dashboard/company-summary"),
  stats: () => http.get<DataResponse<DashboardStats>>("/dashboard/stats"),
  departments: () => http.get<ListResponse<DepartmentStat>>("/dashboard/departments"),
  employees: () => http.get<ListResponse<EmployeeDirectoryItem>>("/dashboard/employees"),
  activity: (limit = 10) =>
    http.get<ListResponse<ActivityItem>>(`/dashboard/activity?limit=${limit}`),
  health: () => http.get<DataResponse<SystemHealth>>("/dashboard/health"),
};
