import type { DataResponse, Department, ListResponse } from "../types";
import { http } from "./client";

export interface DepartmentInput {
  company_id: string;
  code: string;
  name: string;
  focus?: string | null;
}

export const departmentsApi = {
  list: (companyId?: string) =>
    http.get<ListResponse<Department>>(
      companyId ? `/departments?company_id=${companyId}` : "/departments",
    ),
  create: (input: DepartmentInput) => http.post<DataResponse<Department>>("/departments", input),
  update: (id: string, input: Partial<Omit<DepartmentInput, "company_id">>) =>
    http.patch<DataResponse<Department>>(`/departments/${id}`, input),
  remove: (id: string) => http.del(`/departments/${id}`),
};
