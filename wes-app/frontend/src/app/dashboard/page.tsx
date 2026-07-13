'use client';

import { Card, StatCard } from '@/components/ui/Card';
import { PageHeader } from '@/components/ui/PageHeader';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useCompanies } from '@/features/company/hooks';
import { useSystemMetadata } from '@/features/system/hooks';

export default function DashboardPage() {
  const metadata = useSystemMetadata();
  const companies = useCompanies();
  const company = companies.data?.data[0];
  const counts = metadata.data?.counts;

  return (
    <div>
      <PageHeader title="Company Dashboard" subtitle="Operational overview of WES." />

      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="Departments" value={counts?.departments ?? '—'} />
        <StatCard label="Employees" value={counts?.employees ?? '—'} />
        <StatCard label="Companies" value={counts?.companies ?? '—'} />
      </div>

      <Card title="Company Profile">
        {companies.isLoading ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : company ? (
          <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <dt className="text-xs uppercase text-slate-400">Name</dt>
              <dd className="font-medium">{company.name}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase text-slate-400">Type</dt>
              <dd>{company.legalType}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase text-slate-400">Status</dt>
              <dd>
                <StatusBadge status={company.status} />
              </dd>
            </div>
            <div>
              <dt className="text-xs uppercase text-slate-400">Mission</dt>
              <dd>{company.mission ?? '—'}</dd>
            </div>
          </dl>
        ) : (
          <p className="text-sm text-slate-500">
            No company record yet. Create one via the API to get started.
          </p>
        )}
      </Card>
    </div>
  );
}
