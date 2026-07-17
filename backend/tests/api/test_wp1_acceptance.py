"""WP1 integration acceptance — the REAL Autonomous Development page flow.

The page sends only a task *title* (no hand-authored modification spec). These
tests prove the workflow now:

* infers intent, DISCOVERS the existing dashboard file, and MODIFIES it (no
  scaffold) for an existing-UI task;
* FAILS (never silently scaffolds) when an existing-code task cannot be resolved;
* still scaffolds a genuinely new module.
"""

from app.core.config import get_settings

DASHBOARD = "frontend/src/pages/Dashboard.tsx"

# A representative slice of the real Founder Dashboard (same <h1> + anchor),
# written into a controlled project root so the title-only flow is deterministic.
DASHBOARD_FIXTURE = """import { StatusBadge } from "../../components/StatusBadge";

export function Dashboard() {
  const company = null;
  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Founder Dashboard</h1>
        </div>
        {company && <StatusBadge status="active" />}
      </div>

      {!company ? (
        <p>No company exists yet.</p>
      ) : (
        <div className="dashboard-grid">grid</div>
      )}
    </div>
  );
}
"""


def _fixture_root(tmp_path, monkeypatch):
    target = tmp_path / DASHBOARD
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(DASHBOARD_FIXTURE)
    # Point the intent resolver at this controlled repo root.
    monkeypatch.setattr(get_settings(), "project_root", str(tmp_path))
    return tmp_path


def test_title_only_modifies_existing_dashboard(client, quality_seeded, tmp_path, monkeypatch):
    _fixture_root(tmp_path, monkeypatch)

    # EXACTLY what the Autonomous Development page sends: a title, nothing else.
    resp = client.post(
        "/api/v1/development/run",
        json={"title": "Add a Welcome Card to the Founder Dashboard"},
    )
    assert resp.status_code == 200, resp.text
    task = resp.json()["data"]
    detail = client.get(f"/api/v1/development/tasks/{task['id']}").json()["data"]
    changes = detail["changes"]

    # MODIFY the existing dashboard — no scaffold files whatsoever.
    assert len(changes) == 1, changes
    change = changes[0]
    assert change["change_type"] == "modify"
    assert change["path"] == DASHBOARD
    assert all(not c["path"].endswith(".py") for c in changes)
    assert all("docs/" not in c["path"] for c in changes)

    # Real modification diff (not a whole-new-file add).
    diff = change["diff"] or ""
    assert "new file mode" not in diff
    assert "100644" in diff and "@@" in diff
    assert "wes-auto-card" in diff

    # The decision trail is logged in the timeline and proves the path taken.
    intent = next(s for s in detail["timeline"] if s["stage"] == "intent")
    assert "MODIFY" in intent["detail"]
    assert "ModificationPlanner" in intent["detail"]
    assert DASHBOARD in intent["detail"]  # Dashboard.tsx was discovered

    # PR carries the real diff.
    pr = detail["pull_request"]
    assert pr is not None and pr["files_changed"] >= 1 and pr["additions"] >= 3


def test_unresolvable_existing_code_task_fails_never_scaffolds(
    client, quality_seeded, tmp_path, monkeypatch
):
    # Empty project root: an existing-code ("page") intent with no resolvable target.
    monkeypatch.setattr(get_settings(), "project_root", str(tmp_path))
    resp = client.post(
        "/api/v1/development/run",
        json={"title": "Update the Billing Settings page"},
    )
    assert resp.status_code == 200, resp.text
    detail = client.get(f"/api/v1/development/tasks/{resp.json()['data']['id']}").json()["data"]
    # It FAILED rather than scaffolding — and produced no scaffold files.
    assert detail["status"] == "failed"
    assert all(not c["path"].endswith(".py") for c in detail["changes"])
    assert detail["changes"] == []


def test_requirements_extracted_verified_and_pr_created(
    client, quality_seeded, tmp_path, monkeypatch
):
    _fixture_root(tmp_path, monkeypatch)
    resp = client.post(
        "/api/v1/development/run",
        json={
            "title": "Update the Founder Dashboard",
            "description": 'Display "Hello Choudhary"\nDisplay current date\nDisplay current time',
        },
    )
    assert resp.status_code == 200, resp.text
    detail = client.get(f"/api/v1/development/tasks/{resp.json()['data']['id']}").json()["data"]

    # Requirements extracted and ALL verified against the generated code.
    plan = detail["plan"]
    assert len(plan["requirements"]) == 3
    assert all(r["satisfied"] for r in plan["verification"])
    verify = next(s for s in detail["timeline"] if s["stage"] == "verification")
    assert "All 3 requirement(s) satisfied" in verify["detail"]

    # The generated code concretely contains each requirement, and a PR exists.
    diff = detail["changes"][0]["diff"]
    assert "Hello Choudhary" in diff
    assert "toLocaleDateString" in diff and "toLocaleTimeString" in diff
    assert detail["status"] == "pr_ready"
    assert detail["pull_request"] is not None


def test_pr_rejected_when_a_requirement_is_missing(
    client, quality_seeded, tmp_path, monkeypatch
):
    _fixture_root(tmp_path, monkeypatch)
    # Force the generated card to OMIT the time requirement, simulating an
    # incomplete implementation — the verifier must reject before any PR.
    import app.services.dev_requirements as req_mod

    real_build = req_mod.build_requirements_card

    def build_without_time(heading, requirements):
        kept = [r for r in requirements if r.kind != "time"]
        return real_build(heading, kept)

    monkeypatch.setattr(
        "app.services.dev_intent.build_requirements_card", build_without_time, raising=False
    )
    # dev_intent imports the symbol lazily inside _card_snippet, so patch the source.
    monkeypatch.setattr(req_mod, "build_requirements_card", build_without_time)

    resp = client.post(
        "/api/v1/development/run",
        json={
            "title": "Update the Founder Dashboard",
            "description": 'Display "Hello Choudhary"\nDisplay current date\nDisplay current time',
        },
    )
    assert resp.status_code == 200, resp.text
    detail = client.get(f"/api/v1/development/tasks/{resp.json()['data']['id']}").json()["data"]

    # PR REJECTED — task returned for changes, NO pull request, missing req reported.
    assert detail["status"] == "changes_requested"
    assert detail["pull_request"] is None
    verify = next(s for s in detail["timeline"] if s["stage"] == "verification")
    assert "REJECTED" in verify["detail"] and "current time" in verify["detail"]
    plan = detail["plan"]
    missing = [r for r in plan["verification"] if not r["satisfied"]]
    assert len(missing) == 1 and missing[0]["kind"] == "time"


def test_genuine_new_module_still_scaffolds(client, quality_seeded, tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "project_root", str(tmp_path))
    resp = client.post(
        "/api/v1/development/run",
        json={"title": "Add a slug helper utility"},
    )
    assert resp.status_code == 200, resp.text
    detail = client.get(f"/api/v1/development/tasks/{resp.json()['data']['id']}").json()["data"]
    changes = detail["changes"]
    # No existing-file reference -> scaffold a new module (CREATE), as intended.
    assert changes and all(c["change_type"] == "create" for c in changes)
    intent = next(s for s in detail["timeline"] if s["stage"] == "intent")
    assert "CREATE new module" in intent["detail"]
