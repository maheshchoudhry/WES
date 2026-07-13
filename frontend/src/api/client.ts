// Thin fetch wrapper that speaks the backend's response envelope.
//
// Success: { data, meta? }. Error: { error: { code, message, details } }.
// On a non-2xx response we throw an ApiError carrying the parsed message.

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";
const API_PREFIX = "/api/v1";

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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${API_PREFIX}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (res.status === 204) {
    return undefined as T;
  }

  let body: unknown = null;
  const text = await res.text();
  if (text) {
    body = JSON.parse(text);
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
