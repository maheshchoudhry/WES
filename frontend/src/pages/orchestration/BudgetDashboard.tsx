import { useEffect, useState } from "react";

import { orchestrationApi, type BudgetStatus, type CostRow } from "../../api/orchestration";
import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { useAsync } from "../../hooks/useAsync";

export function BudgetDashboard() {
  const { data, loading, error, reload } = useAsync<{
    budget: BudgetStatus;
    cost: CostRow[];
  }>(async () => {
    const [budget, cost] = await Promise.all([
      orchestrationApi.budget(),
      orchestrationApi.cost("day"),
    ]);
    return { budget: budget.data, cost: cost.data };
  }, []);
  const [form, setForm] = useState({
    daily_cost_limit: "",
    monthly_cost_limit: "",
    max_cost: "",
    max_tokens: "",
    warning_threshold: "",
    hard_stop: true,
  });

  useEffect(() => {
    if (data) {
      const c = data.budget.config;
      setForm({
        daily_cost_limit: c.daily_cost_limit?.toString() ?? "",
        monthly_cost_limit: c.monthly_cost_limit?.toString() ?? "",
        max_cost: c.max_cost?.toString() ?? "",
        max_tokens: c.max_tokens?.toString() ?? "",
        warning_threshold: c.warning_threshold?.toString() ?? "",
        hard_stop: c.hard_stop,
      });
    }
  }, [data]);

  if (loading) return <Loading label="Loading budget…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;
  const b = data.budget;

  async function save() {
    const num = (v: string) => (v === "" ? undefined : Number(v));
    await orchestrationApi.updateBudget({
      daily_cost_limit: num(form.daily_cost_limit),
      monthly_cost_limit: num(form.monthly_cost_limit),
      max_cost: num(form.max_cost),
      max_tokens: num(form.max_tokens),
      warning_threshold: num(form.warning_threshold),
      hard_stop: form.hard_stop,
    });
    reload();
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Budget Dashboard</h1>
          <p>Spend guardrails. Hard stop blocks execution before any provider is contacted.</p>
        </div>
      </div>

      <div className="grid stats span-all">
        <StatCard
          label="Daily Spent"
          value={`$${b.daily_spent.toFixed(4)}`}
          hint={b.config.daily_cost_limit ? `of $${b.config.daily_cost_limit}` : "no limit"}
          accent={b.daily_pct >= 1 ? "warn" : "ok"}
        />
        <StatCard
          label="Monthly Spent"
          value={`$${b.monthly_spent.toFixed(4)}`}
          hint={b.config.monthly_cost_limit ? `of $${b.config.monthly_cost_limit}` : "no limit"}
          accent={b.monthly_pct >= 1 ? "warn" : "ok"}
        />
        <StatCard
          label="Status"
          value={b.exceeded ? "Exceeded" : b.warning ? "Warning" : "Healthy"}
          accent={b.exceeded ? "warn" : b.warning ? "warn" : "ok"}
        />
        <StatCard label="Hard Stop" value={b.config.hard_stop ? "On" : "Off"} />
      </div>

      <SectionCard title="Configure Budget">
        <div style={{ display: "grid", gap: 10, maxWidth: 420 }}>
          {(
            [
              ["daily_cost_limit", "Daily cost limit ($)"],
              ["monthly_cost_limit", "Monthly cost limit ($)"],
              ["max_cost", "Max cost per run ($)"],
              ["max_tokens", "Max tokens per run"],
              ["warning_threshold", "Warning threshold (0-1)"],
            ] as const
          ).map(([key, label]) => (
            <label key={key}>
              {label}
              <input
                aria-label={label}
                value={form[key]}
                onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                placeholder="unset"
              />
            </label>
          ))}
          <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <input
              type="checkbox"
              checked={form.hard_stop}
              onChange={(e) => setForm((f) => ({ ...f, hard_stop: e.target.checked }))}
            />
            Hard stop when a limit is reached
          </label>
          <div>
            <button className="btn btn-primary" onClick={save}>
              Save Budget
            </button>
          </div>
        </div>
      </SectionCard>

      <SectionCard title="Today's Cost by Provider">
        {data.cost.length === 0 ? (
          <p className="muted">No spend recorded today.</p>
        ) : (
          <div className="quick-actions">
            {data.cost.map((c) => (
              <span key={c.key ?? c.label} className="badge prio-low">
                {c.label}: ${c.cost.toFixed(4)}
              </span>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}
