import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, http } from "../api/client";

function mockFetch(status: number, body: unknown) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    headers: { get: () => "application/json" },
    text: async () => (body === undefined ? "" : JSON.stringify(body)),
  });
}

function mockTextResponse(status: number, text: string, contentType: string) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    headers: { get: () => contentType },
    text: async () => text,
  });
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("http client", () => {
  it("returns the parsed body on success", async () => {
    vi.stubGlobal("fetch", mockFetch(200, { data: { id: "1" } }));
    const res = await http.get<{ data: { id: string } }>("/companies");
    expect(res.data.id).toBe("1");
  });

  it("returns undefined for 204 No Content", async () => {
    vi.stubGlobal("fetch", mockFetch(204, undefined));
    const res = await http.del("/companies/1");
    expect(res).toBeUndefined();
  });

  it("throws ApiError carrying code and message on error responses", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch(409, { error: { code: "CONFLICT", message: "duplicate", details: [] } }),
    );
    await expect(http.post("/companies", {})).rejects.toMatchObject({
      name: "ApiError",
      status: 409,
      code: "CONFLICT",
      message: "duplicate",
    });
  });

  it("ApiError is an Error instance", () => {
    const e = new ApiError(404, "NOT_FOUND", "missing");
    expect(e).toBeInstanceOf(Error);
    expect(e.code).toBe("NOT_FOUND");
  });

  it("throws INVALID_RESPONSE when the body is HTML (misrouted /api)", async () => {
    vi.stubGlobal("fetch", mockTextResponse(200, "<!doctype html><html></html>", "text/html"));
    await expect(http.get("/dashboard/stats")).rejects.toMatchObject({
      name: "ApiError",
      code: "INVALID_RESPONSE",
    });
  });

  it("throws NETWORK_ERROR when fetch rejects (backend unreachable)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    await expect(http.get("/dashboard/stats")).rejects.toMatchObject({
      name: "ApiError",
      code: "NETWORK_ERROR",
    });
  });
});
