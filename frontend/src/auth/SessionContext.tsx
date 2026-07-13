import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { authApi, type AuthUser } from "../api/auth";
import { authEvents } from "./authEvents";
import { tokenStore } from "./tokenStore";

type Status = "loading" | "authenticated" | "unauthenticated";

interface SessionValue {
  user: AuthUser | null;
  status: Status;
  login: (email: string, password: string, remember: boolean) => Promise<AuthUser>;
  logout: () => Promise<void>;
}

const SessionContext = createContext<SessionValue | undefined>(undefined);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [status, setStatus] = useState<Status>("loading");

  // Hydrate an existing session on mount.
  useEffect(() => {
    let active = true;
    if (!tokenStore.hasSession) {
      setStatus("unauthenticated");
      return;
    }
    authApi
      .me()
      .then((res) => {
        if (!active) return;
        setUser(res.data);
        setStatus("authenticated");
      })
      .catch(() => {
        if (!active) return;
        tokenStore.clear();
        setStatus("unauthenticated");
      });
    return () => {
      active = false;
    };
  }, []);

  // When the API client detects an unrecoverable 401, drop the session.
  useEffect(() => {
    return authEvents.onUnauthorized(() => {
      tokenStore.clear();
      setUser(null);
      setStatus("unauthenticated");
    });
  }, []);

  const value = useMemo<SessionValue>(
    () => ({
      user,
      status,
      async login(email, password, remember) {
        const res = await authApi.login(email, password, remember);
        const { user: authUser, tokens } = res.data;
        tokenStore.set(tokens.access_token, tokens.refresh_token, remember);
        setUser(authUser);
        setStatus("authenticated");
        return authUser;
      },
      async logout() {
        try {
          await authApi.logout();
        } catch {
          // best-effort; clear locally regardless
        }
        tokenStore.clear();
        setUser(null);
        setStatus("unauthenticated");
      },
    }),
    [user, status],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionValue {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within a SessionProvider");
  return ctx;
}
