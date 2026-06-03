export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

class ApiClient {
  async fetch(endpoint: string, options: RequestInit = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    const response = await fetch(url, { ...options, headers });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    if (response.status !== 204) {
      return response.json();
    }
  }

  get(endpoint: string, options?: RequestInit) {
    return this.fetch(endpoint, { ...options, method: "GET" });
  }

  post(endpoint: string, body: any, options?: RequestInit) {
    return this.fetch(endpoint, {
      ...options,
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  put(endpoint: string, body: any, options?: RequestInit) {
    return this.fetch(endpoint, {
      ...options,
      method: "PUT",
      body: JSON.stringify(body),
    });
  }

  delete(endpoint: string, options?: RequestInit) {
    return this.fetch(endpoint, { ...options, method: "DELETE" });
  }
}

export const api = new ApiClient();
