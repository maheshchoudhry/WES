import { Link } from "react-router-dom";

export function Forbidden() {
  return (
    <div className="status-page">
      <div className="status-code">403</div>
      <h1>Forbidden</h1>
      <p className="muted">Your role does not have permission to perform that action.</p>
      <Link to="/" className="btn btn-primary">
        Back to Dashboard
      </Link>
    </div>
  );
}
