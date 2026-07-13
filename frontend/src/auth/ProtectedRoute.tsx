import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { Loading } from "../components/States";
import { useSession } from "./SessionContext";

/** Gate a route behind authentication; redirect unauthenticated users to /login. */
export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { status } = useSession();
  const location = useLocation();

  if (status === "loading") {
    return <Loading label="Checking your session…" />;
  }
  if (status === "unauthenticated") {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <>{children}</>;
}
