import type { Article, ArticleState } from "../types/article";
import type { PaginatedResponse } from "../types/api";
import { api } from "./api-client";

export interface ArticleListParams {
  feed_id?: number;
  state?: ArticleState;
  source?: string;
  limit?: number;
  offset?: number;
}

export async function getArticles(params: ArticleListParams = {}): Promise<PaginatedResponse<Article>> {
  const query: Record<string, string | number> = {
    limit: params.limit ?? 20,
    offset: params.offset ?? 0,
  };
  if (params.feed_id !== undefined) query.feed_id = params.feed_id;
  if (params.state !== undefined) query.state = params.state;
  if (params.source !== undefined) query.source = params.source;
  return api.get<PaginatedResponse<Article>>("/articles", query);
}

export async function getArticle(id: number): Promise<Article> {
  return api.get<Article>(`/articles/${id}`);
}

export async function updateArticleState(id: number, state: ArticleState): Promise<Article> {
  return api.patch<Article>(`/articles/${id}`, { state });
}
