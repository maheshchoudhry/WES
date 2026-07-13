import type { ActivityItem } from "../../api/dashboard";

function relativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const seconds = Math.max(0, Math.round((Date.now() - then) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  return `${days}d ago`;
}

const ICON: Record<ActivityItem["entity_type"], string> = {
  company: "C",
  department: "D",
  employee: "E",
};

/** Reusable activity feed widget. */
export function ActivityFeed({ items }: { items: ActivityItem[] }) {
  if (items.length === 0) {
    return <p className="muted">No recent activity.</p>;
  }
  return (
    <ul className="activity">
      {items.map((item) => (
        <li key={`${item.entity_type}-${item.entity_id}-${item.timestamp}`}>
          <span className={`activity-icon activity-${item.entity_type}`}>
            {ICON[item.entity_type]}
          </span>
          <span className="activity-body">
            <span className="activity-label">{item.label}</span>
            <span className="muted">
              {item.entity_type} {item.action}
            </span>
          </span>
          <time className="muted activity-time">{relativeTime(item.timestamp)}</time>
        </li>
      ))}
    </ul>
  );
}
