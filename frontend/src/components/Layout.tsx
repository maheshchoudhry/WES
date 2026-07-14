import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

import { useSession } from "../auth/SessionContext";

// Active navigation.
const primary = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/company", label: "Company", end: false },
  { to: "/departments", label: "Departments", end: false },
  { to: "/employees", label: "Employees", end: false },
];

// AI Company (Sprint 06).
const aiNav = [
  { to: "/ai", label: "AI Company", end: true },
  { to: "/ai/directory", label: "AI Directory", end: false },
  { to: "/ai/org", label: "AI Org Chart", end: false },
];

// Work Management (Sprint 07).
const workNav = [
  { to: "/projects", label: "Projects", end: false },
  { to: "/board", label: "Task Board", end: false },
];

// Execution Engine (Sprint 08).
const execNav = [
  { to: "/execution/workspace", label: "AI Workspace", end: false },
  { to: "/execution/queue", label: "Execution Queue", end: false },
  { to: "/execution/reviews", label: "Review Queue", end: false },
  { to: "/execution/prompts", label: "Prompt Library", end: false },
  { to: "/execution/sops", label: "SOP Library", end: false },
  { to: "/execution/performance", label: "Performance", end: false },
];

// Reserved for future sprints — shown disabled so the shell is production-ready.
const reserved = ["Knowledge", "Reports", "Settings"];

const ROLE_LABEL: Record<string, string> = {
  founder: "Founder",
  director: "Director",
  department_head: "Department Head",
  employee: "Employee",
  read_only: "Read Only",
};

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useSession();

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          WES OS
          <small>Founder Workspace</small>
        </div>
        <nav className="nav">
          {primary.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end}>
              {l.label}
            </NavLink>
          ))}
        </nav>
        <div className="nav-reserved">
          <div className="nav-reserved-label">Work</div>
          {workNav.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end}>
              {l.label}
            </NavLink>
          ))}
        </div>
        <div className="nav-reserved">
          <div className="nav-reserved-label">AI Company</div>
          {aiNav.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end}>
              {l.label}
            </NavLink>
          ))}
        </div>
        <div className="nav-reserved">
          <div className="nav-reserved-label">Execution</div>
          {execNav.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end}>
              {l.label}
            </NavLink>
          ))}
        </div>
        <div className="nav-reserved">
          <div className="nav-reserved-label">Coming soon</div>
          {reserved.map((label) => (
            <span key={label} className="nav-disabled" aria-disabled="true">
              {label}
            </span>
          ))}
        </div>
        {user && (
          <div className="sidebar-user">
            <div className="user-name">{user.full_name}</div>
            <div className="user-role">{ROLE_LABEL[user.role] ?? user.role}</div>
            <button className="btn btn-sm logout-btn" onClick={() => logout()}>
              Sign out
            </button>
          </div>
        )}
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
