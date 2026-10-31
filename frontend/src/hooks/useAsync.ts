import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../services/api";

/** Runs an async loader and exposes loading/error state plus a reload function. */
export function useAsync<T>(loader: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(() => {
    setLoading(true);
    return loader()
      .then((value) => { setData(value); setError(null); })
      .catch((e: unknown) => setError(e instanceof ApiError ? e.message : "Unexpected error"))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => { void reload(); }, [reload]);
  return { data, error, loading, reload, setData };
}
