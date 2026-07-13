import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

// Active navigation (Sprint 03 scope).
const primary = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/company", label: "Company", end: false },
  { to: "/departments", label: "Departments", end: false },
  { to: "/employees", label: "Employees", end: false },
];

// Reserved for future sprints — shown disabled so the shell is production-ready.
const reserved = ["Projects", "Tasks", "Knowledge", "Reports", "AI Hub", "Settings"];

export function Layout({ children }: { children: ReactNode }) {
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
          <div className="nav-reserved-label">Coming soon</div>
          {reserved.map((label) => (
            <span key={label} className="nav-disabled" aria-disabled="true">
              {label}
            </span>
          ))}
        </div>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
