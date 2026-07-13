import { Link } from "react-router-dom";

export function Unauthorized() {
  return (
    <div className="status-page">
      <div className="status-code">401</div>
      <h1>Unauthorized</h1>
      <p className="muted">Your session has expired or you are not signed in.</p>
      <Link to="/login" className="btn btn-primary">
        Go to Sign in
      </Link>
    </div>
  );
}
