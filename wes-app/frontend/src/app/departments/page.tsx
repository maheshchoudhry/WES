'use client';

import { Column, DataTable } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Department } from '@/features/departments/types';
import { useDepartments } from '@/features/departments/hooks';

const columns: Column<Department>[] = [
  { header: 'Code', cell: (d) => <span className="font-mono text-xs">{d.code}</span> },
  { header: 'Name', cell: (d) => <span className="font-medium">{d.name}</span> },
  { header: 'Focus', cell: (d) => d.focus ?? '—' },
  { header: 'Status', cell: (d) => <StatusBadge status={d.status} /> },
];

export default function DepartmentsPage() {
  const { data, isLoading, isError } = useDepartments();

  return (
    <div>
      <PageHeader title="Departments" subtitle="WES departments and their focus." />
      {isLoading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : isError ? (
        <p className="text-sm text-red-600">Failed to load departments.</p>
      ) : (
        <DataTable columns={columns} rows={data?.data ?? []} empty="No departments yet." />
      )}
    </div>
  );
}
