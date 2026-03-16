export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface ProblemDetail {
  type: string;
  title: string;
  status: number;
  detail: string;
  [key: string]: unknown;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly title: string,
    public readonly detail: string,
    public readonly raw: ProblemDetail,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

export interface SyncResult {
  fetched: number;
  feed_id: number;
  title: string;
}

export interface SyncAllResponse {
  data: SyncResult[];
  total: number;
}
