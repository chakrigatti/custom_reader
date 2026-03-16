import type { Article, ArticleState } from "../types/article";
import { NEXT_STATE } from "../types/article";
import { getArticles, updateArticleState, type ArticleListParams } from "../services/article-service";
import { relativeTime } from "../utils/date";
import { showToast } from "./toast";

export interface ArticleListCallbacks {
  onSelectArticle: (id: number) => void;
}

const PAGE_SIZE = 20;

let container: HTMLElement;
let callbacks: ArticleListCallbacks;
let articles: Article[] = [];
let currentParams: ArticleListParams = {};
let total = 0;
let scrollTop = 0;

export function mountArticleList(el: HTMLElement, cbs: ArticleListCallbacks): void {
  container = el;
  callbacks = cbs;
}

export function saveScroll(): void {
  scrollTop = container.scrollTop;
}

export async function loadArticles(params: ArticleListParams = {}): Promise<void> {
  currentParams = { ...params, limit: PAGE_SIZE, offset: 0 };
  container.innerHTML = `<div class="loading">Loading articles...</div>`;
  try {
    const result = await getArticles(currentParams);
    articles = result.data;
    total = result.total;
  } catch {
    articles = [];
    total = 0;
  }
  scrollTop = 0;
  render();
}

export function restoreView(): void {
  render();
  container.scrollTop = scrollTop;
}

async function loadMore(): Promise<void> {
  const btn = container.querySelector(".load-more") as HTMLButtonElement | null;
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Loading...";
  }
  const offset = articles.length;
  try {
    const result = await getArticles({ ...currentParams, offset });
    articles = [...articles, ...result.data];
    total = result.total;
  } catch (err) {
    showToast(err instanceof Error ? err.message : "Failed to load more", "error");
  }
  render();
}

function render(): void {
  if (articles.length === 0) {
    container.innerHTML = `<div class="empty-state">No articles found.</div>`;
    return;
  }

  const rows = articles.map((a) => {
    const unread = a.state === "unread" ? "article-row--unread" : "";
    const stateLabel = a.state === "read_again" ? "re-read" : a.state;
    return `<div class="article-row ${unread}" data-id="${a.id}">
      <div class="article-row-main">
        <span class="article-title">${escapeHtml(a.title)}</span>
        <span class="article-meta">${relativeTime(a.published_at)}</span>
      </div>
      <div class="article-row-sub">
        <button class="btn-state" data-id="${a.id}" data-state="${a.state}" title="Mark as ${NEXT_STATE[a.state]}">${stateLabel}</button>
      </div>
    </div>`;
  }).join("");

  const moreBtn = articles.length < total
    ? `<button class="btn btn--secondary load-more">Load more</button>`
    : "";

  container.innerHTML = `<div class="article-list">${rows}</div>${moreBtn}`;

  container.querySelectorAll(".article-row").forEach((row) => {
    row.addEventListener("click", (e) => {
      if ((e.target as HTMLElement).classList.contains("btn-state")) return;
      callbacks.onSelectArticle(Number((row as HTMLElement).dataset.id));
    });
  });

  container.querySelector(".load-more")?.addEventListener("click", loadMore);

  container.querySelectorAll(".btn-state").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const el = btn as HTMLElement;
      const id = Number(el.dataset.id);
      const current = el.dataset.state as ArticleState;
      const next = NEXT_STATE[current];
      const article = articles.find((a) => a.id === id);
      if (!article) return;

      // Optimistic update
      const prev = article.state;
      article.state = next;
      render();

      try {
        await updateArticleState(id, next);
      } catch {
        article.state = prev;
        render();
        showToast("Failed to update state", "error");
      }
    });
  });
}

function escapeHtml(s: string): string {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}
