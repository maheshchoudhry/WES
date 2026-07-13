export function Loading({ label = "Loading…" }: { label?: string }) {
  return <div className="empty">{label}</div>;
}

export function ErrorNotice({ message }: { message: string }) {
  return (
    <div className="notice notice-error" role="alert">
      {message}
    </div>
  );
}

export function Empty({ message }: { message: string }) {
  return <div className="empty">{message}</div>;
}
