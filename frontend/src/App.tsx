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
import { Conversation } from "./pages/orchestration/Conversation";
import { Executions } from "./pages/orchestration/Executions";
import { ProviderSettings } from "./pages/orchestration/ProviderSettings";
import { ProviderDashboard } from "./pages/orchestration/ProviderDashboard";
import { BudgetDashboard } from "./pages/orchestration/BudgetDashboard";
import { ExecutionMonitor } from "./pages/orchestration/ExecutionMonitor";
import { StreamingViewer } from "./pages/orchestration/StreamingViewer";
import { ConnectionTester } from "./pages/orchestration/ConnectionTester";
import { AdvancedSearch } from "./pages/knowledge/AdvancedSearch";
import { ArchitectureDecisions } from "./pages/knowledge/ArchitectureDecisions";
import { Bookmarks } from "./pages/knowledge/Bookmarks";
import { CategoryExplorer } from "./pages/knowledge/CategoryExplorer";
import { Collections } from "./pages/knowledge/Collections";
import { DocumentEditor } from "./pages/knowledge/DocumentEditor";
import { DocumentViewer } from "./pages/knowledge/DocumentViewer";
import { KnowledgeDashboard } from "./pages/knowledge/KnowledgeDashboard";
import { KnowledgeGraph } from "./pages/knowledge/KnowledgeGraph";
import { KnowledgeLibrary } from "./pages/knowledge/KnowledgeLibrary";
import { ReviewCenter } from "./pages/knowledge/ReviewCenter";
import { AIWorkspace } from "./pages/execution/AIWorkspace";
import { ExecutionHistory } from "./pages/execution/ExecutionHistory";
import { ExecutionQueue } from "./pages/execution/ExecutionQueue";
import { PerformanceDashboard } from "./pages/execution/PerformanceDashboard";
import { PromptLibrary } from "./pages/execution/PromptLibrary";
import { ReviewQueue } from "./pages/execution/ReviewQueue";
import { SOPLibrary } from "./pages/execution/SOPLibrary";
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
        <Route path="/execution/workspace" element={<AIWorkspace />} />
        <Route path="/execution/queue" element={<ExecutionQueue />} />
        <Route path="/execution/reviews" element={<ReviewQueue />} />
        <Route path="/execution/history" element={<ExecutionHistory />} />
        <Route path="/execution/performance" element={<PerformanceDashboard />} />
        <Route path="/execution/prompts" element={<PromptLibrary />} />
        <Route path="/execution/sops" element={<SOPLibrary />} />
        <Route path="/orchestration/runs" element={<Executions />} />
        <Route path="/orchestration/threads/:threadId" element={<Conversation />} />
        <Route path="/orchestration/monitor" element={<ExecutionMonitor />} />
        <Route path="/orchestration/streaming" element={<StreamingViewer />} />
        <Route path="/settings/providers" element={<ProviderSettings />} />
        <Route path="/providers/dashboard" element={<ProviderDashboard />} />
        <Route path="/providers/budget" element={<BudgetDashboard />} />
        <Route path="/providers/connection-test" element={<ConnectionTester />} />
        <Route path="/knowledge" element={<KnowledgeDashboard />} />
        <Route path="/knowledge/library" element={<KnowledgeLibrary />} />
        <Route path="/knowledge/new" element={<DocumentEditor />} />
        <Route path="/knowledge/documents/:id" element={<DocumentViewer />} />
        <Route path="/knowledge/documents/:id/edit" element={<DocumentEditor />} />
        <Route path="/knowledge/categories" element={<CategoryExplorer />} />
        <Route path="/knowledge/graph" element={<KnowledgeGraph />} />
        <Route path="/knowledge/collections" element={<Collections />} />
        <Route path="/knowledge/bookmarks" element={<Bookmarks />} />
        <Route path="/knowledge/reviews" element={<ReviewCenter />} />
        <Route path="/knowledge/adrs" element={<ArchitectureDecisions />} />
        <Route path="/knowledge/search" element={<AdvancedSearch />} />
        <Route path="/forbidden" element={<Forbidden />} />
      </Route>
    </Routes>
  );
}
