import { useCallback, useEffect, useState } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export function useApi<T>(path: string, fallback: T) {
  const [data, setData] = useState<T>(fallback);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get<T>(`${API_URL}${path}`);
      setData(response.data);
    } catch (err) {
      console.error('Failed to load', path, err);
      setError('Unable to load data');
      setData(fallback);
    } finally {
      setLoading(false);
    }
  }, [path, fallback]);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  return { data, loading, error, refresh: fetchData };
}

export const apiBaseUrl = API_URL;
