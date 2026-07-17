import { useState } from "react";

import { companyApi, type Conversation, type TimelineEvent } from "../../api/company";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { useAsync } from "../../hooks/useAsync";

const TYPE_TONE: Record<string, string> = {
  project_created: "badge-active",
  approval: "prio-medium",
  approval_needed: "prio-high",
  deployment: "badge-active",
  pipeline: "prio-medium",
  handoff: "prio-low",
  stage: "prio-low",
  project_execution: "prio-medium",
};

function fmt(at: string | null): string {
  if (!at) return "";
  try {
    return new Date(at).toLocaleString();
  } catch {
    return at;
  }
}

/** Founder Executive Timeline (Parts 7 & 10) + Agent Conversations (Part 4).
 * Every event and message comes from real runtime records. Filterable by type
 * and free-text search. */
export function ExecutiveTimeline() {
  const [q, setQ] = useState("");
  const [type, setType] = useState("all");
  const { data, loading, error } = useAsync<{ events: TimelineEvent[]; convos: Conversation[] }>(
    async () => {
      const [events, convos] = await Promise.all([
        companyApi.timeline().then((r) => r.data),
        companyApi.conversations().then((r) => r.data),
      ]);
      return { events, convos };
    },
    [],
  );

  if (loading) return <Loading label="Loading executive timeline…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;

  const types = ["all", ...Array.from(new Set(data.events.map((e) => e.type)))];
  const events = data.events.filter(
    (e) =>
      (type === "all" || e.type === type) &&
      (!q || (e.title + (e.actor ?? "")).toLowerCase().includes(q.toLowerCase())),
  );

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Executive Timeline</h1>
          <p>The autonomous company at work — every event from real runtime.</p>
        </div>
      </div>

      <div className="card" style={{ display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
        <input
          aria-label="Search timeline"
          placeholder="Search events…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          style={{ flex: 1, minWidth: 200 }}
        />
        <select aria-label="Filter type" value={type} onChange={(e) => setType(e.target.value)}>
          {types.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      <div className="cmd-layout">
        <div className="cmd-main">
          <SectionCard title={`Company Timeline (${events.length})`}>
            {events.length === 0 ? (
              <Empty message="No events yet. Approve a project plan to start the company." />
            ) : (
              <div className="timeline">
                {events.map((e, i) => (
                  <div key={i} className="timeline-row" data-testid="timeline-event">
                    <span className="timeline-dot" aria-hidden="true" />
                    <div className="timeline-body">
                      <div className="timeline-head">
                        <span className={`badge ${TYPE_TONE[e.type] ?? "prio-low"}`}>{e.type}</span>
                        <span className="timeline-title">{e.title}</span>
                      </div>
                      <div className="muted timeline-meta">
                        {e.actor ? `${e.actor} · ` : ""}
                        {fmt(e.at)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
        </div>

        <aside className="cmd-aside">
          <SectionCard title="Agent Conversations">
            {data.convos.length === 0 ? (
              <Empty message="No agent messages yet." />
            ) : (
              <div className="mini-list">
                {data.convos.slice(0, 20).map((m, i) => (
                  <div key={i} className="convo-item" data-testid="convo-item">
                    <div className="convo-head">
                      <strong>{m.from}</strong> → <strong>{m.to}</strong>
                      {m.task && <span className="badge prio-low">{m.task}</span>}
                    </div>
                    <div className="muted">{m.message}</div>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
        </aside>
      </div>
    </div>
  );
}
