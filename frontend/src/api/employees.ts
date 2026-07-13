import type {
  AuthorityLevel,
  DataResponse,
  Employee,
  EmployeeStatus,
  ListResponse,
} from "../types";
import { http } from "./client";

export interface EmployeeInput {
  company_id: string;
  department_id?: string | null;
  reports_to_id?: string | null;
  employee_code: string;
  full_name: string;
  email: string;
  position: string;
  authority?: AuthorityLevel;
  status?: EmployeeStatus;
}

export const employeesApi = {
  list: (params: { companyId?: string; departmentId?: string } = {}) => {
    const q = new URLSearchParams();
    if (params.companyId) q.set("company_id", params.companyId);
    if (params.departmentId) q.set("department_id", params.departmentId);
    const qs = q.toString();
    return http.get<ListResponse<Employee>>(`/employees${qs ? `?${qs}` : ""}`);
  },
  register: (input: EmployeeInput) => http.post<DataResponse<Employee>>("/employees", input),
  update: (id: string, input: Partial<Omit<EmployeeInput, "company_id" | "employee_code">>) =>
    http.patch<DataResponse<Employee>>(`/employees/${id}`, input),
  assignDepartment: (id: string, departmentId: string | null) =>
    http.put<DataResponse<Employee>>(`/employees/${id}/department`, {
      department_id: departmentId,
    }),
  remove: (id: string) => http.del(`/employees/${id}`),
};
