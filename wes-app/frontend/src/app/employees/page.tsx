'use client';

import { Column, DataTable } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Employee } from '@/features/employees/types';
import { useEmployees } from '@/features/employees/hooks';

const columns: Column<Employee>[] = [
  {
    header: 'Code',
    cell: (e) => <span className="font-mono text-xs">{e.employeeCode}</span>,
  },
  { header: 'Name', cell: (e) => <span className="font-medium">{e.name}</span> },
  { header: 'Position', cell: (e) => e.position },
  { header: 'Department', cell: (e) => e.departmentName ?? '—' },
  { header: 'State', cell: (e) => <StatusBadge status={e.operationalState} /> },
];

export default function EmployeesPage() {
  const { data, isLoading, isError } = useEmployees();

  return (
    <div>
      <PageHeader title="Employees" subtitle="WES AI workforce." />
      {isLoading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : isError ? (
        <p className="text-sm text-red-600">Failed to load employees.</p>
      ) : (
        <DataTable columns={columns} rows={data?.data ?? []} empty="No employees yet." />
      )}
    </div>
  );
}
