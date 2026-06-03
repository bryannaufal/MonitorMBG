import { useEffect, useState } from "react";

export function useSSE(url: string) {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      try {
        setData(JSON.parse(event.data));
      } catch (e) {
        setData(event.data);
      }
    };

    eventSource.onerror = (err) => {
      setError(new Error("SSE connection error"));
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [url]);

  return { data, error };
}
