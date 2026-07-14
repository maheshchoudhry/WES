import { useEffect, useState } from "react";

import { qualityApi, type QualityFounderDash, type QualityReport } from "../../api/quality";

/** Loads the founder aggregate + the most-recent task's full quality report. */
export function useQualityReport() {
  const [dash, setDash] = useState<QualityFounderDash | null>(null);
  const [report, setReport] = useState<QualityReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const d = (await qualityApi.founderDashboard()).data;
        if (!active) return;
        setDash(d);
        const taskId = d.recent[0]?.task_id;
        if (taskId) {
          const r = (await qualityApi.report(taskId)).data;
          if (active) setReport(r);
        }
      } catch (e) {
        if (active) setError(e instanceof Error ? e.message : "Failed to load");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  return { dash, report, loading, error };
}
