import { Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { CompanyOverview } from "./pages/CompanyOverview";
import { Dashboard } from "./pages/Dashboard";
import { DepartmentsPage } from "./pages/DepartmentsPage";
import { EmployeesPage } from "./pages/EmployeesPage";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/company" element={<CompanyOverview />} />
        <Route path="/departments" element={<DepartmentsPage />} />
        <Route path="/employees" element={<EmployeesPage />} />
      </Routes>
    </Layout>
  );
}
