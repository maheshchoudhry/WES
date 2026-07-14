import { useEffect, useState } from "react";

import { repositoryApi, type Repository } from "../../api/repository";

/** Loads the first registered repository (the engine hosts one primary repo). */
export function useRepository() {
  const [repo, setRepo] = useState<Repository | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    repositoryApi
      .list()
      .then((r) => active && setRepo(r.data[0] ?? null))
      .catch((e) => active && setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  return { repo, loading, error };
}
