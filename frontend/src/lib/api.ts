export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
  ) {
    super(message);
  }
}

class ApiClient {
  async fetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = options.body instanceof FormData
      ? { ...options.headers }
      : {
          "Content-Type": "application/json",
          ...options.headers,
        };

    const requestInit: RequestInit = { ...options, headers };
    if (requestInit.method === "GET") requestInit.cache = "no-store";
    const response = await fetch(url, requestInit);

    if (!response.ok) {
      throw new ApiError(`API error: ${response.status} ${response.statusText}`, response.status);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json() as Promise<T>;
  }

  get<T>(endpoint: string, options?: RequestInit) {
    return this.fetch<T>(endpoint, { ...options, method: "GET" });
  }

  post<T, TBody = unknown>(endpoint: string, body: TBody, options?: RequestInit) {
    return this.fetch<T>(endpoint, {
      ...options,
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  postForm<T>(endpoint: string, body: FormData) {
    const url = `${API_BASE_URL}${endpoint}`;
    return fetch(url, { method: "POST", body, cache: "no-store" }).then(async (response) => {
      if (!response.ok) {
        let detail = `${response.status} ${response.statusText}`;
        try {
          const err = (await response.json()) as { detail?: string | { msg?: string }[] };
          if (typeof err.detail === "string") detail = err.detail;
          else if (Array.isArray(err.detail) && err.detail[0]?.msg) detail = err.detail[0].msg;
        } catch {
          /* ignore */
        }
        throw new ApiError(`API error: ${detail}`, response.status);
      }
      return response.json() as Promise<T>;
    });
  }

  patch<T, TBody = unknown>(endpoint: string, body: TBody, options?: RequestInit) {
    return this.fetch<T>(endpoint, {
      ...options,
      method: "PATCH",
      body: JSON.stringify(body),
    });
  }
}

export const api = new ApiClient();

export async function getWithFallback<T>(
  endpoint: string,
  fallback: T,
): Promise<{ data: T; source: "api" | "fallback"; error?: string }> {
  try {
    const data = await api.get<T>(endpoint);
    return { data, source: "api" };
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown API error";
    return { data: fallback, source: "fallback", error: message };
  }
}
