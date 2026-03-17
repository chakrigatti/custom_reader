import { ApiError, type ProblemDetail } from "../types/api";

class ApiClient {
  async get<T>(path: string, params?: Record<string, string | number>): Promise<T> {
    const url = params ? `${path}?${new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    )}` : path;
    return this.request<T>("GET", url);
  }

  async post<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>("POST", path, body);
  }

  async patch<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>("PATCH", path, body);
  }

  async put<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>("PUT", path, body);
  }

  async del(path: string): Promise<void> {
    await this.request<void>("DELETE", path);
  }

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    let response: Response;
    try {
      response = await fetch(path, {
        method,
        headers: body !== undefined ? { "Content-Type": "application/json" } : {},
        body: body !== undefined ? JSON.stringify(body) : undefined,
      });
    } catch {
      throw new ApiError(0, "Network Error", "Cannot reach server. Is the API running?", {
        type: "about:blank",
        title: "Network Error",
        status: 0,
        detail: "Cannot reach server. Is the API running?",
      });
    }

    if (response.status === 204) {
      return undefined as T;
    }

    if (!response.ok) {
      let problem: ProblemDetail;
      try {
        problem = await response.json();
      } catch {
        problem = {
          type: "about:blank",
          title: response.statusText,
          status: response.status,
          detail: `HTTP ${response.status} ${response.statusText}`,
        };
      }
      throw new ApiError(problem.status, problem.title, problem.detail, problem);
    }

    return response.json();
  }
}

export const api = new ApiClient();
