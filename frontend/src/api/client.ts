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
  const url = `${BASE_URL}${API_PREFIX}${path}`;

  let res: Response;
  try {
    res = await fetch(url, {
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      ...init,
    });
  } catch {
    // fetch() itself rejected: the API is unreachable (wrong URL, backend down,
    // CORS blocked). Surface an actionable message instead of a bare TypeError.
    throw new ApiError(
      0,
      "NETWORK_ERROR",
      `Could not reach the API at ${url}. Is the backend running and the API URL / proxy configured?`,
    );
  }

  if (res.status === 204) {
    return undefined as T;
  }

  const text = await res.text();

  // Parse the body as JSON. A non-JSON body (commonly an HTML index.html served
  // by a static host when /api is not proxied to the backend) is a configuration
  // problem, not a valid API response — report it clearly.
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
