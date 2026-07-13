import { Link } from "react-router-dom";

export interface QuickAction {
  label: string;
  to: string;
  disabled?: boolean;
}

/** Reusable quick-navigation widget. */
export function QuickActions({ actions }: { actions: QuickAction[] }) {
  return (
    <div className="quick-actions">
      {actions.map((a) =>
        a.disabled ? (
          <span key={a.label} className="btn quick-action disabled" aria-disabled="true">
            {a.label}
            <small>Soon</small>
          </span>
        ) : (
          <Link key={a.label} to={a.to} className="btn quick-action">
            {a.label}
          </Link>
        ),
      )}
    </div>
  );
}
