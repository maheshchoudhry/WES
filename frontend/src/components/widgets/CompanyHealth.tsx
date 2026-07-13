import type { SystemHealth } from "../../api/dashboard";
import { StatusBadge } from "../StatusBadge";

/** Reusable system/company health widget. */
export function CompanyHealth({ health }: { health: SystemHealth }) {
  const dbOk = health.database === "connected";
  return (
    <div className="health">
      <div className="health-row">
        <span>API</span>
        <StatusBadge status={health.api === "ok" ? "active" : "inactive"} />
      </div>
      <div className="health-row">
        <span>Database</span>
        <StatusBadge status={dbOk ? "active" : "inactive"} />
      </div>
      <div className="health-row">
        <span>Version</span>
        <span className="muted">v{health.version}</span>
      </div>
    </div>
  );
}
