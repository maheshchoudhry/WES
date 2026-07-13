// Thin fetch wrapper that speaks the backend's response envelope and handles
// authentication: it attaches the access token, transparently refreshes it once
// on a 401, and signals the app shell on auth failures.
//
// Success: { data, meta? }. Error: { error: { code, message, details } }.

import { authEvents } from "../auth/authEvents";
import { tokenStore } from "../auth/tokenStore";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";
const API_PREFIX = "/api/v1";

// Endpoints that must never trigger the refresh-and-retry loop.
const NO_REFRESH = ["/auth/login", "/auth/refresh", "/auth/logout"];

export class ApiError extends Error {
  code: string;
  status: number;
  details: unknown[];

  constructor(status: number, code: string, message: string, details: unknown[] = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function rawRequest<T>(path: string, init: RequestInit, withAuth: boolean): Promise<T> {
  const url = `${BASE_URL}${API_PREFIX}${path}`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...((init.headers as Record<string, string>) ?? {}),
  };
  if (withAuth && tokenStore.access) {
    headers.Authorization = `Bearer ${tokenStore.access}`;
  }

  let res: Response;
  try {
    res = await fetch(url, { ...init, headers });
  } catch {
    throw new ApiError(
      0,
      "NETWORK_ERROR",
      `Could not reach the API at ${url}. Is the backend running and the API URL / proxy configured?`,
    );
  }

  if (res.status === 204) return undefined as T;

  const text = await res.text();
  let body: unknown = null;
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      const contentType = res.headers.get("content-type") ?? "unknown";
      throw new ApiError(
        res.status,
        "INVALID_RESPONSE",
        `Expected JSON from the API but received "${contentType}". ` +
          "The request likely did not reach the backend — check VITE_API_BASE_URL " +
          "or the dev/nginx proxy for /api.",
      );
    }
  }

  if (!res.ok) {
    const err = (body as { error?: { code: string; message: string; details?: unknown[] } })
      ?.error;
    throw new ApiError(
      res.status,
      err?.code ?? "ERROR",
      err?.message ?? `Request failed with status ${res.status}`,
      err?.details ?? [],
    );
  }

  return body as T;
}

async function tryRefresh(): Promise<boolean> {
  const refreshToken = tokenStore.refresh;
  if (!refreshToken) return false;
  try {
    const res = await rawRequest<{ data: { tokens: { access_token: string } } }>(
      "/auth/refresh",
      { method: "POST", body: JSON.stringify({ refresh_token: refreshToken }) },
      false,
    );
    tokenStore.setAccess(res.data.tokens.access_token);
    return true;
  } catch {
    return false;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const eligible = !NO_REFRESH.includes(path.split("?")[0]);
  try {
    return await rawRequest<T>(path, init, true);
  } catch (err) {
    if (!(err instanceof ApiError)) throw err;

    if (err.status === 403) {
      authEvents.emitForbidden();
      throw err;
    }

    if (err.status === 401 && eligible) {
      if (await tryRefresh()) {
        try {
          return await rawRequest<T>(path, init, true);
        } catch (retryErr) {
          if (retryErr instanceof ApiError && retryErr.status === 401) {
            tokenStore.clear();
            authEvents.emitUnauthorized();
          }
          throw retryErr;
        }
      }
      tokenStore.clear();
      authEvents.emitUnauthorized();
    }
    throw err;
  }
}

export const http = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, data: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(data) }),
  patch: <T>(path: string, data: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(data) }),
  put: <T>(path: string, data: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(data) }),
  del: (path: string) => request<void>(path, { method: "DELETE" }),
};
