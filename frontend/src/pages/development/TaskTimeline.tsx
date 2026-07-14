import { Link, useParams } from "react-router-dom";

import { developmentApi, type DevStage, stageLabel } from "../../api/development";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

export function TaskTimeline() {
  const { id = "" } = useParams();
  const { data, loading, error } = useAsync<DevStage[]>(
    () => developmentApi.timeline(id).then((r) => r.data),
    [id],
  );
  if (loading) return <Loading label="Loading timeline…" />;
  if (error) return <ErrorNotice message={error} />;
  const stages = data ?? [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Task Timeline</h1>
          <p>Stage-by-stage execution of the autonomous workflow.</p>
        </div>
        <Link to={`/development/tasks/${id}`} className="btn">
          Back to Task
        </Link>
      </div>

      <SectionCard title="Workflow Stages">
        {stages.length === 0 ? (
          <Empty message="No timeline yet." />
        ) : (
          <ul className="activity">
            {stages.map((s, i) => (
              <li key={i}>
                <span className="activity-body">
                  <span className="activity-label">
                    {i + 1}. {stageLabel(s.stage)}
                    {s.role ? ` · ${s.role}` : ""}
                  </span>
                  <span className="activity-time">{s.detail}</span>
                </span>
                <StatusBadge status={s.status} />
              </li>
            ))}
          </ul>
        )}
      </SectionCard>
    </div>
  );
}
