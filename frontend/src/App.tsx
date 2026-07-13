import { useEffect } from "react";
import { Outlet, Route, Routes, useNavigate } from "react-router-dom";

import { authEvents } from "./auth/authEvents";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { Layout } from "./components/Layout";
import { CompanyOverview } from "./pages/CompanyOverview";
import { Dashboard } from "./pages/Dashboard";
import { DepartmentsPage } from "./pages/DepartmentsPage";
import { EmployeesPage } from "./pages/EmployeesPage";
import { Forbidden } from "./pages/Forbidden";
import { Login } from "./pages/Login";
import { Unauthorized } from "./pages/Unauthorized";

function ProtectedLayout() {
  return (
    <ProtectedRoute>
      <Layout>
        <Outlet />
      </Layout>
    </ProtectedRoute>
  );
}

export default function App() {
  const navigate = useNavigate();

  // When the API client reports a 403, route to the Forbidden page.
  useEffect(() => authEvents.onForbidden(() => navigate("/forbidden")), [navigate]);

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/unauthorized" element={<Unauthorized />} />

      <Route element={<ProtectedLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/company" element={<CompanyOverview />} />
        <Route path="/departments" element={<DepartmentsPage />} />
        <Route path="/employees" element={<EmployeesPage />} />
        <Route path="/forbidden" element={<Forbidden />} />
      </Route>
    </Routes>
  );
}
