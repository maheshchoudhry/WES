import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { workApi, type ProjectIntakeInput } from "../../api/work";
import { SectionCard } from "../../components/widgets";

/** Founder Project Intake — capture a business objective and submit it to the AI
 * CEO for analysis + decomposition. Creating a project does NOT begin
 * implementation; it produces a plan for Founder approval. */
export function ProjectIntake() {
  const navigate = useNavigate();
  const [f, setF] = useState({
    code: "",
    name: "",
    priority: "medium",
    repository: "",
    business_objective: "",
    business_problem: "",
    intake_description: "",
    acceptance_criteria: "",
    deliverables: "",
    constraints: "",
    timeline: "",
    founder_notes: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function set<K extends keyof typeof f>(key: K, value: string) {
    setF((prev) => ({ ...prev, [key]: value }));
  }

  const lines = (v: string) =>
    v
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const input: ProjectIntakeInput = {
        code: f.code,
        name: f.name,
        priority: f.priority,
        repository: f.repository || undefined,
        business_objective: f.business_objective || undefined,
        business_problem: f.business_problem || undefined,
        intake_description: f.intake_description || undefined,
        acceptance_criteria: f.acceptance_criteria || undefined,
        deliverables: lines(f.deliverables),
        constraints: lines(f.constraints),
        timeline: f.timeline || undefined,
        founder_notes: f.founder_notes || undefined,
      };
      const project = (await workApi.createProject(input)).data;
      // Submit to the AI CEO: analysis + automatic decomposition (no implementation).
      await workApi.decompose(project.id);
      navigate(`/projects/${project.id}/plan`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed");
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>New Project — Founder Intake</h1>
          <p>Describe the business objective. The AI CEO will analyse and plan it.</p>
        </div>
      </div>

      <form onSubmit={submit}>
        <SectionCard title="Project">
          <div className="intake-grid">
            <div className="field">
              <label htmlFor="i-code">Project Number</label>
              <input
                id="i-code"
                value={f.code}
                onChange={(e) => set("code", e.target.value)}
                placeholder="PROJ-002"
                required
              />
            </div>
            <div className="field">
              <label htmlFor="i-name">Project Name</label>
              <input
                id="i-name"
                value={f.name}
                onChange={(e) => set("name", e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="i-priority">Priority</label>
              <select
                id="i-priority"
                value={f.priority}
                onChange={(e) => set("priority", e.target.value)}
              >
                {["critical", "high", "medium", "low"].map((x) => (
                  <option key={x} value={x}>
                    {x}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="i-repo">Repository</label>
              <input
                id="i-repo"
                value={f.repository}
                onChange={(e) => set("repository", e.target.value)}
                placeholder="optional"
              />
            </div>
            <div className="field">
              <label htmlFor="i-timeline">Timeline</label>
              <input
                id="i-timeline"
                value={f.timeline}
                onChange={(e) => set("timeline", e.target.value)}
                placeholder="e.g. 2 sprints"
              />
            </div>
          </div>
        </SectionCard>

        <SectionCard title="Business">
          <div className="field">
            <label htmlFor="i-objective">Business Objective</label>
            <textarea
              id="i-objective"
              rows={2}
              value={f.business_objective}
              onChange={(e) => set("business_objective", e.target.value)}
              placeholder="What business outcome should this achieve?"
              required
            />
          </div>
          <div className="field">
            <label htmlFor="i-problem">Business Problem</label>
            <textarea
              id="i-problem"
              rows={2}
              value={f.business_problem}
              onChange={(e) => set("business_problem", e.target.value)}
              placeholder="What problem are we solving?"
            />
          </div>
          <div className="field">
            <label htmlFor="i-desc">Detailed Description</label>
            <textarea
              id="i-desc"
              rows={4}
              value={f.intake_description}
              onChange={(e) => set("intake_description", e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="i-accept">Acceptance Criteria</label>
            <textarea
              id="i-accept"
              rows={3}
              value={f.acceptance_criteria}
              onChange={(e) => set("acceptance_criteria", e.target.value)}
              placeholder="How do we know it's done?"
            />
          </div>
        </SectionCard>

        <SectionCard title="Scope">
          <div className="intake-grid">
            <div className="field">
              <label htmlFor="i-deliv">Expected Deliverables (one per line)</label>
              <textarea
                id="i-deliv"
                rows={4}
                value={f.deliverables}
                onChange={(e) => set("deliverables", e.target.value)}
                placeholder={"Inventory API\nInventory Dashboard\nStock Alerts"}
              />
            </div>
            <div className="field">
              <label htmlFor="i-constraints">Constraints (one per line)</label>
              <textarea
                id="i-constraints"
                rows={4}
                value={f.constraints}
                onChange={(e) => set("constraints", e.target.value)}
                placeholder={"Reuse existing auth\nNo new database engine"}
              />
            </div>
          </div>
          <div className="field">
            <label htmlFor="i-notes">Founder Notes</label>
            <textarea
              id="i-notes"
              rows={2}
              value={f.founder_notes}
              onChange={(e) => set("founder_notes", e.target.value)}
            />
          </div>
        </SectionCard>

        {error && <div className="form-error">{error}</div>}

        <div className="modal-actions" style={{ marginTop: 16 }}>
          <button type="button" className="btn" onClick={() => navigate("/projects")}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? "Submitting to AI CEO…" : "Submit to AI CEO"}
          </button>
        </div>
      </form>
    </div>
  );
}
