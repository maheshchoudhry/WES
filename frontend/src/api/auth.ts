import type { DataResponse } from "../types";
import { http } from "./client";

export type Role = "founder" | "director" | "department_head" | "employee" | "read_only";

export interface AuthUser {
  id: string;
  employee_code: string;
  full_name: string;
  email: string;
  role: Role;
  department_id: string | null;
  status: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginResult {
  user: AuthUser;
  tokens: TokenPair;
}

export const authApi = {
  login: (email: string, password: string, remember: boolean) =>
    http.post<DataResponse<LoginResult>>("/auth/login", { email, password, remember }),
  logout: () => http.post<DataResponse<{ status: string }>>("/auth/logout", {}),
  me: () => http.get<DataResponse<AuthUser>>("/auth/me"),
  refresh: (refreshToken: string) =>
    http.post<DataResponse<{ tokens: TokenPair }>>("/auth/refresh", {
      refresh_token: refreshToken,
    }),
};
