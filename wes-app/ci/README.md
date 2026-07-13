# CI Workflow (staging)

This directory holds the GitHub Actions pipeline for the WES Web Application.

The workflow lives here — not in `.github/workflows/` — because the automation token used to commit it lacks the **Workflows** permission. Enable CI with either option:

## Option A — move the file (simplest)

Copy [`github-actions-ci.yml`](./github-actions-ci.yml) to `.github/workflows/ci.yml` and commit it:

```bash
mkdir -p .github/workflows
cp wes-app/ci/github-actions-ci.yml .github/workflows/ci.yml
git add .github/workflows/ci.yml && git commit -m "ci: enable GitHub Actions pipeline" && git push
```

## Option B — grant the token Workflows permission

On the fine-grained token: **Repository permissions → Workflows → Read and write**, then re-run the automation to push the workflow.

## What it does

On every push and pull request to `main`:

- **Backend:** install deps, `ruff` lint, `alembic upgrade head` against PostgreSQL, DB persistence check, `pytest`.
- **Frontend:** install deps, ESLint, Vitest, `next build`.

The pipeline fails if any step fails.
