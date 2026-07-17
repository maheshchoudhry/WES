import { useEffect, useState, type ReactNode } from "react";
import { NavLink, useLocation } from "react-router-dom";

import { useSession } from "../auth/SessionContext";

type NavItem = { to: string; label: string; end?: boolean; soon?: boolean };
type NavGroup = { id: string; icon: string; label: string; items: NavItem[] };

// Every existing route is preserved and reorganized into logical, collapsible
// groups. Items marked `soon` have no backing page yet (they mirror the existing
// "coming soon" treatment) — they are never linked and add no fake data.
const GROUPS: NavGroup[] = [
  {
    id: "founder",
    icon: "🏠",
    label: "Founder",
    items: [
      { to: "/", label: "Dashboard", end: true },
      { to: "/company/live", label: "Live Company" },
      { to: "/company/timeline", label: "Executive Timeline" },
      { to: "/notifications", label: "Notifications" },
    ],
  },
  {
    id: "company",
    icon: "🏢",
    label: "Company",
    items: [
      { to: "/company", label: "Company" },
      { to: "/departments", label: "Departments" },
      { to: "/employees", label: "Employees" },
      { to: "/#org-health", label: "Organization Health", soon: true },
    ],
  },
  {
    id: "ai",
    icon: "🤖",
    label: "AI Organization",
    items: [
      { to: "/ai", label: "AI Company", end: true },
      { to: "/ai/directory", label: "AI Directory" },
      { to: "/ai/org", label: "AI Org Chart" },
      { to: "/ai/departments", label: "AI Departments" },
      { to: "/execution/workspace", label: "AI Workspaces" },
      { to: "/execution/performance", label: "Performance" },
      { to: "/#ai-roles", label: "AI Roles", soon: true },
    ],
  },
  {
    id: "projects",
    icon: "📁",
    label: "Project Management",
    items: [
      { to: "/projects", label: "Projects" },
      { to: "/projects/new", label: "New Project" },
      { to: "/board", label: "Task Board" },
      { to: "/#milestones", label: "Milestones", soon: true },
      { to: "/#sprints", label: "Sprints", soon: true },
      { to: "/#activity", label: "Activity", soon: true },
    ],
  },
  {
    id: "execution",
    icon: "⚙️",
    label: "Execution",
    items: [
      { to: "/execution/queue", label: "Execution Queue" },
      { to: "/execution/reviews", label: "Review Queue" },
      { to: "/execution/history", label: "Execution History" },
      { to: "/execution/prompts", label: "Prompt Library" },
      { to: "/execution/sops", label: "SOP Library" },
    ],
  },
  {
    id: "knowledge",
    icon: "🧠",
    label: "Knowledge",
    items: [
      { to: "/knowledge", label: "Knowledge", end: true },
      { to: "/knowledge/library", label: "Library" },
      { to: "/knowledge/search", label: "Search" },
      { to: "/knowledge/graph", label: "Knowledge Graph" },
      { to: "/knowledge/categories", label: "Categories" },
      { to: "/knowledge/collections", label: "Collections" },
      { to: "/knowledge/bookmarks", label: "Bookmarks" },
      { to: "/knowledge/reviews", label: "Review Center" },
      { to: "/knowledge/adrs", label: "Architecture Decisions" },
    ],
  },
  {
    id: "repository",
    icon: "📦",
    label: "Repository",
    items: [
      { to: "/repository", label: "Repository", end: true },
      { to: "/repository/explorer", label: "Explorer" },
      { to: "/repository/architecture", label: "Architecture" },
      { to: "/repository/dependencies", label: "Dependency Graph" },
      { to: "/repository/symbols", label: "Symbols" },
      { to: "/repository/search", label: "Code Search" },
      { to: "/repository/impact", label: "Impact Analysis" },
      { to: "/repository/modules", label: "Modules" },
    ],
  },
  {
    id: "development",
    icon: "🧩",
    label: "Autonomous Development",
    items: [
      { to: "/development", label: "Development", end: true },
      { to: "/development/team", label: "AI Team" },
      { to: "/quality/review", label: "Code Reviews" },
      { to: "/development/pull-requests", label: "Pull Requests" },
      { to: "/development/approvals", label: "Approval Center" },
      { to: "/quality", label: "Quality Gates", end: true },
      { to: "/quality/security", label: "Security" },
      { to: "/quality/performance", label: "Performance" },
      { to: "/quality/risk", label: "Risk Analysis" },
      { to: "/quality/release", label: "Release Readiness" },
      { to: "/learning", label: "Self-Learning" },
      { to: "/#repo-changes", label: "Repository Changes", soon: true },
    ],
  },
  {
    id: "devops",
    icon: "🚀",
    label: "DevOps",
    items: [
      { to: "/devops", label: "Pipelines", end: true },
      { to: "/devops/releases", label: "Releases" },
      { to: "/devops/deployments", label: "Deployments" },
      { to: "/devops/monitoring", label: "Monitoring" },
      { to: "/devops/rollback", label: "Rollback" },
      { to: "/devops/incidents", label: "Incidents" },
      { to: "/devops/environments", label: "Environments" },
    ],
  },
  {
    id: "providers",
    icon: "🔌",
    label: "AI Providers",
    items: [
      { to: "/providers/dashboard", label: "Providers" },
      { to: "/settings/providers", label: "Provider Settings" },
      { to: "/orchestration/runs", label: "Executions" },
      { to: "/orchestration/monitor", label: "Execution Monitor" },
      { to: "/orchestration/streaming", label: "Streaming" },
      { to: "/providers/budget", label: "Budgets" },
      { to: "/providers/connection-test", label: "Connection Tester" },
      { to: "/#models", label: "Models", soon: true },
      { to: "/#cost", label: "Cost", soon: true },
      { to: "/#usage", label: "Usage", soon: true },
    ],
  },
  {
    id: "admin",
    icon: "🛠️",
    label: "Administration",
    items: [
      { to: "/devops/monitoring", label: "System Health" },
      { to: "/audit", label: "Audit Logs" },
      { to: "/#settings", label: "Settings", soon: true },
      { to: "/#integrations", label: "Integrations", soon: true },
    ],
  },
];

const ROLE_LABEL: Record<string, string> = {
  founder: "Founder",
  director: "Director",
  department_head: "Department Head",
  employee: "Employee",
  read_only: "Read Only",
};

const STORAGE_KEY = "wes.nav.collapsed";

function activeGroupId(pathname: string): string {
  // The group whose (non-soon) item best matches the current path.
  let best = "";
  let bestLen = -1;
  for (const g of GROUPS) {
    for (const it of g.items) {
      if (it.soon) continue;
      const p = it.to;
      const match = p === "/" ? pathname === "/" : pathname === p || pathname.startsWith(p + "/");
      if (match && p.length > bestLen) {
        bestLen = p.length;
        best = g.id;
      }
    }
  }
  return best || "founder";
}

function loadCollapsed(): Set<string> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return new Set(JSON.parse(raw) as string[]);
  } catch {
    /* ignore */
  }
  // Default: only the Founder group open; the rest collapsed to reduce clutter.
  return new Set(GROUPS.filter((g) => g.id !== "founder").map((g) => g.id));
}

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useSession();
  const { pathname } = useLocation();
  const active = activeGroupId(pathname);
  const [collapsed, setCollapsed] = useState<Set<string>>(loadCollapsed);

  // Auto-expand the group that owns the current route.
  useEffect(() => {
    setCollapsed((prev) => {
      if (!prev.has(active)) return prev;
      const next = new Set(prev);
      next.delete(active);
      return next;
    });
  }, [active]);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify([...collapsed]));
    } catch {
      /* ignore */
    }
  }, [collapsed]);

  function toggle(id: string) {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          WES OS
          <small>Command Center</small>
        </div>
        <nav className="nav nav-grouped">
          {GROUPS.map((g) => {
            const open = !collapsed.has(g.id);
            return (
              <div key={g.id} className={`nav-group${open ? "" : " collapsed"}`}>
                <button
                  type="button"
                  className={`nav-group-header${g.id === active ? " active-group" : ""}`}
                  aria-expanded={open}
                  onClick={() => toggle(g.id)}
                >
                  <span className="nav-group-icon" aria-hidden="true">
                    {g.icon}
                  </span>
                  <span className="nav-group-label">{g.label}</span>
                  <span className="nav-chevron" aria-hidden="true">
                    {open ? "▾" : "▸"}
                  </span>
                </button>
                {open && (
                  <div className="nav-group-items">
                    {g.items.map((it) =>
                      it.soon ? (
                        <span
                          key={it.label}
                          className="nav-item nav-disabled"
                          aria-disabled="true"
                          title="Planned — not yet available"
                        >
                          {it.label}
                          <span className="nav-soon">soon</span>
                        </span>
                      ) : (
                        <NavLink key={it.to} to={it.to} end={it.end} className="nav-item">
                          {it.label}
                        </NavLink>
                      ),
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </nav>
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
