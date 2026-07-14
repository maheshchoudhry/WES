import { useState } from "react";
import { Link } from "react-router-dom";

import { developmentApi, type DevTask } from "../../api/development";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

export function PullRequestCenter() {
  const { data, loading, error } = useAsync<DevTask[]>(async () => {
    const tasks = await developmentApi.tasks();
    // Load full detail (with PR) for tasks that reached a PR.
    const withPr = tasks.data.filter((t) =>
      ["pr_ready", "approved", "rejected", "changes_requested"].includes(t.status),
    );
    const details = await Promise.all(
      withPr.map((t) => developmentApi.task(t.id).then((r) => r.data)),
    );
    return details.filter((d) => d.pull_request);
  }, []);
  const [open, setOpen] = useState<string | null>(null);

  if (loading) return <Loading label="Loading pull requests…" />;
  if (error) return <ErrorNotice message={error} />;
  const tasks = data ?? [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Pull Request Center</h1>
          <p>
            Autonomously prepared pull-request drafts. Not pushed, not merged — Founder approves.
          </p>
        </div>
      </div>

      {tasks.length === 0 ? (
        <Empty message="No pull requests yet." />
      ) : (
        tasks.map((t) => {
          const pr = t.pull_request!;
          return (
            <SectionCard
              key={t.id}
              title={pr.title}
              action={
                <button className="btn btn-sm" onClick={() => setOpen(open === t.id ? null : t.id)}>
                  {open === t.id ? "Hide" : "View draft"}
                </button>
              }
            >
              <p className="muted">
                <StatusBadge status={pr.status} /> {pr.branch_name} → {pr.base_branch} ·{" "}
                {pr.commit_count} commits · {pr.files_changed} files · +{pr.additions}/−
                {pr.deletions} · <Link to={`/development/tasks/${t.id}`}>{t.code}</Link>
              </p>
              {open === t.id && (
                <>
                  <h4>Body</h4>
                  <pre
                    className="chat-content"
                    style={{ whiteSpace: "pre-wrap", maxHeight: 240, overflow: "auto" }}
                  >
                    {pr.body}
                  </pre>
                  <h4>Release Notes</h4>
                  <pre className="chat-content" style={{ whiteSpace: "pre-wrap" }}>
                    {pr.release_notes}
                  </pre>
                </>
              )}
            </SectionCard>
          );
        })
      )}
    </div>
  );
}
