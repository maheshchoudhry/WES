// Shared domain types, mirroring the backend schemas.

export type EntityStatus = "active" | "inactive" | "archived";
export type EmployeeStatus = "onboarding" | "active" | "inactive" | "archived";
export type AuthorityLevel = "executive" | "lead" | "operational";

export interface Company {
  id: string;
  name: string;
  slug: string;
  company_type: string;
  purpose: string | null;
  description: string | null;
  status: EntityStatus;
  created_at: string;
  updated_at: string;
}

export interface Department {
  id: string;
  company_id: string;
  code: string;
  name: string;
  focus: string | null;
  status: EntityStatus;
  created_at: string;
  updated_at: string;
}

export interface Employee {
  id: string;
  company_id: string;
  department_id: string | null;
  reports_to_id: string | null;
  employee_code: string;
  full_name: string;
  email: string;
  position: string;
  authority: AuthorityLevel;
  status: EmployeeStatus;
  created_at: string;
  updated_at: string;
}

export interface ListMeta {
  total?: number;
  page?: number;
  page_size?: number;
}

export interface DataResponse<T> {
  data: T;
  meta?: ListMeta;
}

export interface ListResponse<T> {
  data: T[];
  meta: ListMeta;
}
