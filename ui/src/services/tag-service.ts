import type { Tag } from "../types/article";
import type { Article } from "../types/article";
import { api } from "./api-client";

export interface TagListResponse {
  data: Tag[];
  total: number;
}

export async function getTags(q?: string): Promise<TagListResponse> {
  const params: Record<string, string> = {};
  if (q) params.q = q;
  return api.get<TagListResponse>("/tags", params);
}

export async function addTagToArticle(articleId: number, name: string): Promise<Article> {
  return api.post<Article>(`/articles/${articleId}/tags`, { name });
}

export async function removeTagFromArticle(articleId: number, tagId: number): Promise<Article> {
  const resp = await fetch(`/articles/${articleId}/tags/${tagId}`, { method: "DELETE" });
  return resp.json();
}
