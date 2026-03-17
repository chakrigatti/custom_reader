export type ArticleState = "unread" | "read" | "read_again";

export interface Tag {
  id: number;
  name: string;
}

export interface Article {
  id: number;
  feed_id: number;
  title: string;
  url: string;
  author: string | null;
  content_html: string;
  content_markdown: string;
  summary: string | null;
  published_at: string | null;
  fetched_at: string;
  state: ArticleState;
  warning?: string | null;
  tags: Tag[];
}

export const NEXT_STATE: Record<ArticleState, ArticleState> = {
  unread: "read",
  read: "read_again",
  read_again: "unread",
};
