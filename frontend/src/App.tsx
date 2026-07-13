import { useEffect } from "react";
import { Outlet, Route, Routes, useNavigate } from "react-router-dom";

import { authEvents } from "./auth/authEvents";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { Layout } from "./components/Layout";
import { AIDashboard } from "./pages/ai/AIDashboard";
import { AIDepartmentView } from "./pages/ai/AIDepartmentView";
import { AIDirectory } from "./pages/ai/AIDirectory";
import { AIOrgChart } from "./pages/ai/AIOrgChart";
import { AIProfile } from "./pages/ai/AIProfile";
import { CompanyOverview } from "./pages/CompanyOverview";
import { Dashboard } from "./pages/Dashboard";
import { DepartmentsPage } from "./pages/DepartmentsPage";
import { EmployeesPage } from "./pages/EmployeesPage";
import { Forbidden } from "./pages/Forbidden";
import { Login } from "./pages/Login";
import { Unauthorized } from "./pages/Unauthorized";
import { KanbanBoard } from "./pages/work/KanbanBoard";
import { ProjectDetail } from "./pages/work/ProjectDetail";
import { ProjectsPage } from "./pages/work/ProjectsPage";
import { TaskDetail } from "./pages/work/TaskDetail";

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
        <Route path="/ai" element={<AIDashboard />} />
        <Route path="/ai/directory" element={<AIDirectory />} />
        <Route path="/ai/org" element={<AIOrgChart />} />
        <Route path="/ai/departments" element={<AIDepartmentView />} />
        <Route path="/ai/employees/:id" element={<AIProfile />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/projects/:id" element={<ProjectDetail />} />
        <Route path="/board" element={<KanbanBoard />} />
        <Route path="/tasks/:id" element={<TaskDetail />} />
        <Route path="/forbidden" element={<Forbidden />} />
      </Route>
    </Routes>
  );
}
