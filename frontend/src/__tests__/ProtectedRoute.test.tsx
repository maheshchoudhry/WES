import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { authApi } from "../api/auth";
import { ProtectedRoute } from "../auth/ProtectedRoute";
import { SessionProvider } from "../auth/SessionContext";
import { tokenStore } from "../auth/tokenStore";

vi.mock("../api/auth");

afterEach(() => {
  tokenStore.clear();
  vi.clearAllMocks();
});

function renderProtected() {
  return render(
    <MemoryRouter initialEntries={["/secret"]}>
      <SessionProvider>
        <Routes>
          <Route
            path="/secret"
            element={
              <ProtectedRoute>
                <div>SECRET CONTENT</div>
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>LOGIN SCREEN</div>} />
        </Routes>
      </SessionProvider>
    </MemoryRouter>,
  );
}

describe("ProtectedRoute", () => {
  it("redirects to login when there is no session", async () => {
    renderProtected();
    await waitFor(() => expect(screen.getByText("LOGIN SCREEN")).toBeInTheDocument());
    expect(screen.queryByText("SECRET CONTENT")).not.toBeInTheDocument();
  });

  it("renders children when authenticated", async () => {
    tokenStore.set("access", "refresh", true);
    vi.mocked(authApi.me).mockResolvedValue({
      data: { id: "1", employee_code: "WES-EMP-001", full_name: "F", email: "f@wes.studio", role: "founder", department_id: null, status: "active" },
    } as never);

    renderProtected();
    await waitFor(() => expect(screen.getByText("SECRET CONTENT")).toBeInTheDocument());
  });
});
