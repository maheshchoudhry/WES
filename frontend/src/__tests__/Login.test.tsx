import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { authApi } from "../api/auth";
import { ApiError } from "../api/client";
import { SessionProvider } from "../auth/SessionContext";
import { tokenStore } from "../auth/tokenStore";
import { Login } from "../pages/Login";

vi.mock("../api/auth");

afterEach(() => {
  tokenStore.clear();
  vi.clearAllMocks();
});

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={["/login"]}>
      <SessionProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<div>DASHBOARD HOME</div>} />
        </Routes>
      </SessionProvider>
    </MemoryRouter>,
  );
}

describe("Login", () => {
  it("logs in and redirects to the dashboard", async () => {
    vi.mocked(authApi.login).mockResolvedValue({
      data: {
        user: { id: "1", employee_code: "WES-EMP-001", full_name: "Studio Director", email: "f@wes.studio", role: "founder", department_id: null, status: "active" },
        tokens: { access_token: "a", refresh_token: "r", token_type: "bearer", expires_in: 1800 },
      },
    } as never);

    renderLogin();
    await userEvent.type(screen.getByLabelText(/email/i), "f@wes.studio");
    await userEvent.type(screen.getByLabelText(/password/i), "WesOs2026!");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => expect(screen.getByText("DASHBOARD HOME")).toBeInTheDocument());
    expect(authApi.login).toHaveBeenCalledWith("f@wes.studio", "WesOs2026!", false);
  });

  it("shows an error on invalid credentials", async () => {
    vi.mocked(authApi.login).mockRejectedValue(new ApiError(401, "UNAUTHORIZED", "bad"));

    renderLogin();
    await userEvent.type(screen.getByLabelText(/email/i), "f@wes.studio");
    await userEvent.type(screen.getByLabelText(/password/i), "wrong");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() =>
      expect(screen.getByText(/invalid email or password/i)).toBeInTheDocument(),
    );
  });
});
