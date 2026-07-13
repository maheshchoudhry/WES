const TONE: Record<string, string> = {
  active: 'bg-green-100 text-green-800',
  available: 'bg-green-100 text-green-800',
  inactive: 'bg-slate-100 text-slate-600',
  assigned: 'bg-blue-100 text-blue-800',
  working: 'bg-blue-100 text-blue-800',
  blocked: 'bg-red-100 text-red-800',
};

export function StatusBadge({ status }: { status: string }) {
  const tone = TONE[status.toLowerCase()] ?? 'bg-slate-100 text-slate-600';
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${tone}`}
    >
      {status}
    </span>
  );
}
