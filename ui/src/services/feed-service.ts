import type { Feed } from "../types/feed";
import type { PaginatedResponse } from "../types/api";
import { api } from "./api-client";

export async function getFeeds(): Promise<PaginatedResponse<Feed>> {
  return api.get<PaginatedResponse<Feed>>("/feeds", { limit: 200 });
}

export async function createFeed(url: string): Promise<Feed> {
  return api.post<Feed>("/feeds", { url });
}

export async function deleteFeed(id: number): Promise<void> {
  return api.del(`/feeds/${id}`);
}
