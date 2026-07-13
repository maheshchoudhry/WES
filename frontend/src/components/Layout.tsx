import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Company Overview", end: true },
  { to: "/departments", label: "Departments", end: false },
  { to: "/employees", label: "Employees", end: false },
];

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          WES OS
          <small>Company Engine</small>
        </div>
        <nav className="nav">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end}>
              {l.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
