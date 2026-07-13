import type { DepartmentStat } from "../../api/dashboard";
import { StatusBadge } from "../StatusBadge";

/** Reusable department summary card. */
export function DepartmentCard({ dept }: { dept: DepartmentStat }) {
  return (
    <div className="card dept-card">
      <div className="dept-card-head">
        <span className="dept-code">{dept.code}</span>
        <StatusBadge status={dept.status} />
      </div>
      <h3>{dept.name}</h3>
      {dept.focus && <p className="muted dept-focus">{dept.focus}</p>}
      <div className="dept-count">
        <strong>{dept.employee_count}</strong> {dept.employee_count === 1 ? "employee" : "employees"}
      </div>
    </div>
  );
}
