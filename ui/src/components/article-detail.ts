import type { ArticleState } from "../types/article";
import { NEXT_STATE } from "../types/article";
import { getArticle, updateArticleState } from "../services/article-service";
import { renderMarkdown } from "../utils/markdown";
import { relativeTime } from "../utils/date";
import { showToast } from "./toast";

export interface ArticleDetailCallbacks {
  onBack: () => void;
}

let container: HTMLElement;
let callbacks: ArticleDetailCallbacks;

export function mountArticleDetail(el: HTMLElement, cbs: ArticleDetailCallbacks): void {
  container = el;
  callbacks = cbs;
}

export async function showArticle(id: number): Promise<void> {
  container.innerHTML = `<div class="loading">Loading...</div>`;

  try {
    const article = await getArticle(id);

    // Auto-mark as read (fire-and-forget)
    if (article.state === "unread") {
      updateArticleState(id, "read").catch(() => {});
      article.state = "read";
    }

    const stateLabel = article.state === "read_again" ? "re-read" : article.state;
    const author = article.author ? `<span class="detail-author">by ${escapeHtml(article.author)}</span>` : "";

    container.innerHTML = `
      <div class="article-detail">
        <div class="detail-toolbar">
          <button class="btn btn--secondary detail-back">&larr; Back</button>
          <div class="detail-toolbar-right">
            <button class="btn btn--secondary detail-state" data-state="${article.state}">
              ${stateLabel}
            </button>
            <a class="btn btn--secondary" href="${escapeAttr(article.url)}" target="_blank" rel="noopener">
              Open original
            </a>
          </div>
        </div>
        <article class="detail-content">
          <h1 class="detail-title">${escapeHtml(article.title)}</h1>
          <div class="detail-meta">
            ${author}
            <span class="detail-date">${relativeTime(article.published_at)}</span>
          </div>
          <div class="detail-body">${renderMarkdown(article.content_markdown || "")}</div>
        </article>
      </div>
    `;

    container.querySelector(".detail-back")!.addEventListener("click", callbacks.onBack);

    const stateBtn = container.querySelector(".detail-state") as HTMLElement;
    stateBtn.addEventListener("click", async () => {
      const current = stateBtn.dataset.state as ArticleState;
      const next = NEXT_STATE[current];
      try {
        await updateArticleState(id, next);
        stateBtn.dataset.state = next;
        stateBtn.textContent = next === "read_again" ? "re-read" : next;
      } catch {
        showToast("Failed to update state", "error");
      }
    });
  } catch (err) {
    container.innerHTML = `<div class="empty-state">${err instanceof Error ? escapeHtml(err.message) : "Article not found."}</div>`;
  }
}

function escapeHtml(s: string): string {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

function escapeAttr(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
