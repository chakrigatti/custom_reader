import type { Category } from "../types/feed";
import type { Feed } from "../types/feed";
import { api } from "./api-client";

export interface CategoryListResponse {
  data: Category[];
  total: number;
}

export async function getCategories(): Promise<CategoryListResponse> {
  return api.get<CategoryListResponse>("/categories");
}

export async function createCategory(name: string): Promise<Category> {
  return api.post<Category>("/categories", { name });
}

export async function renameCategory(id: number, name: string): Promise<Category> {
  return api.patch<Category>(`/categories/${id}`, { name });
}

export async function deleteCategory(id: number): Promise<void> {
  return api.del(`/categories/${id}`);
}

export async function setFeedCategories(feedId: number, categoryIds: number[]): Promise<Feed> {
  return api.put<Feed>(`/feeds/${feedId}/categories`, { category_ids: categoryIds });
}
