import type { Company, DataResponse, ListResponse } from "../types";
import { http } from "./client";

export interface CompanyInput {
  name: string;
  slug: string;
  company_type: string;
  purpose?: string | null;
  description?: string | null;
}

export const companiesApi = {
  list: () => http.get<ListResponse<Company>>("/companies"),
  get: (id: string) => http.get<DataResponse<Company>>(`/companies/${id}`),
  create: (input: CompanyInput) => http.post<DataResponse<Company>>("/companies", input),
  update: (id: string, input: Partial<CompanyInput>) =>
    http.patch<DataResponse<Company>>(`/companies/${id}`, input),
  remove: (id: string) => http.del(`/companies/${id}`),
};
