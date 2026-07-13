import { useState } from "react";

import { companiesApi, type CompanyInput } from "../api/companies";
import { departmentsApi } from "../api/departments";
import { employeesApi } from "../api/employees";
import { Modal } from "../components/Modal";
import { ErrorNotice, Loading } from "../components/States";
import { StatusBadge } from "../components/StatusBadge";
import { useAsync } from "../hooks/useAsync";
import type { Company } from "../types";

interface Overview {
  company: Company | null;
  departments: number;
  employees: number;
}

async function loadOverview(): Promise<Overview> {
  const [companies, departments, employees] = await Promise.all([
    companiesApi.list(),
    departmentsApi.list(),
    employeesApi.list(),
  ]);
  return {
    company: companies.data[0] ?? null,
    departments: departments.meta.total ?? departments.data.length,
    employees: employees.meta.total ?? employees.data.length,
  };
}

export function CompanyOverview() {
  const { data, loading, error, reload } = useAsync(loadOverview, []);
  const [editing, setEditing] = useState(false);
  const [creating, setCreating] = useState(false);

  if (loading) return <Loading />;
  if (error) return <ErrorNotice message={error} />;

  const company = data?.company ?? null;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Company Overview</h1>
          <p>The root of the WES organization.</p>
        </div>
        {company ? (
          <button className="btn" onClick={() => setEditing(true)}>
            Edit Company
          </button>
        ) : (
          <button className="btn btn-primary" onClick={() => setCreating(true)}>
            Create Company
          </button>
        )}
      </div>

      {!company ? (
        <div className="card">
          <p className="muted">No company exists yet. Create one to begin.</p>
        </div>
      ) : (
        <>
          <div className="grid stats" style={{ marginBottom: 20 }}>
            <div className="card stat">
              <div className="value">{data?.departments}</div>
              <div className="label">Departments</div>
            </div>
            <div className="card stat">
              <div className="value">{data?.employees}</div>
              <div className="label">Employees</div>
            </div>
            <div className="card stat">
              <div className="value">
                <StatusBadge status={company.status} />
              </div>
              <div className="label">Status</div>
            </div>
          </div>

          <div className="card">
            <h2 style={{ marginTop: 0 }}>{company.name}</h2>
            <p className="muted">{company.company_type}</p>
            <dl style={{ display: "grid", gridTemplateColumns: "140px 1fr", rowGap: 8 }}>
              <dt className="muted">Slug</dt>
              <dd style={{ margin: 0 }}>{company.slug}</dd>
              <dt className="muted">Purpose</dt>
              <dd style={{ margin: 0 }}>{company.purpose ?? "—"}</dd>
              <dt className="muted">Description</dt>
              <dd style={{ margin: 0 }}>{company.description ?? "—"}</dd>
            </dl>
          </div>
        </>
      )}

      {creating && (
        <CompanyForm
          title="Create Company"
          onClose={() => setCreating(false)}
          onSubmit={async (input) => {
            await companiesApi.create(input);
            setCreating(false);
            reload();
          }}
        />
      )}
      {editing && company && (
        <CompanyForm
          title="Edit Company"
          initial={company}
          onClose={() => setEditing(false)}
          onSubmit={async (input) => {
            await companiesApi.update(company.id, {
              name: input.name,
              company_type: input.company_type,
              purpose: input.purpose,
              description: input.description,
            });
            setEditing(false);
            reload();
          }}
        />
      )}
    </div>
  );
}

interface FormProps {
  title: string;
  initial?: Company;
  onClose: () => void;
  onSubmit: (input: CompanyInput) => Promise<void>;
}

function CompanyForm({ title, initial, onClose, onSubmit }: FormProps) {
  const [name, setName] = useState(initial?.name ?? "");
  const [slug, setSlug] = useState(initial?.slug ?? "");
  const [companyType, setCompanyType] = useState(initial?.company_type ?? "");
  const [purpose, setPurpose] = useState(initial?.purpose ?? "");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await onSubmit({ name, slug, company_type: companyType, purpose });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title={title} onClose={onClose}>
      <form onSubmit={submit}>
        <div className="field">
          <label htmlFor="c-name">Name</label>
          <input id="c-name" value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="field">
          <label htmlFor="c-slug">Slug</label>
          <input
            id="c-slug"
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            disabled={!!initial}
            placeholder="e.g. wes"
            required
          />
        </div>
        <div className="field">
          <label htmlFor="c-type">Type</label>
          <input
            id="c-type"
            value={companyType}
            onChange={(e) => setCompanyType(e.target.value)}
            required
          />
        </div>
        <div className="field">
          <label htmlFor="c-purpose">Purpose</label>
          <textarea
            id="c-purpose"
            value={purpose ?? ""}
            onChange={(e) => setPurpose(e.target.value)}
            rows={3}
          />
        </div>
        {error && <div className="form-error">{error}</div>}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? "Saving…" : "Save"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
