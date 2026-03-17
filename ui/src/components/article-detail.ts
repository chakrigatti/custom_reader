import type { Article, ArticleState, Tag } from "../types/article";
import { NEXT_STATE } from "../types/article";
import { getArticle, updateArticleState } from "../services/article-service";
import { addTagToArticle, removeTagFromArticle, getTags } from "../services/tag-service";
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

    renderArticle(id, article);
  } catch (err) {
    container.innerHTML = `<div class="empty-state">${err instanceof Error ? escapeHtml(err.message) : "Article not found."}</div>`;
  }
}

function renderArticle(id: number, article: Article): void {
  const stateLabel = article.state === "read_again" ? "re-read" : article.state;
  const author = article.author ? `<span class="detail-author">by ${escapeHtml(article.author)}</span>` : "";

  const tagsHtml = renderTags(article.tags);

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
        <div class="detail-tags" id="detail-tags">
          ${tagsHtml}
          <div class="tag-input-wrapper">
            <input type="text" class="tag-input" placeholder="Add tag..." id="tag-input">
            <div class="tag-suggestions" id="tag-suggestions"></div>
          </div>
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

  // Tag removal
  container.querySelectorAll(".tag-chip-remove").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const tagId = Number((btn as HTMLElement).dataset.tagId);
      try {
        const updated = await removeTagFromArticle(id, tagId);
        article.tags = updated.tags;
        renderArticle(id, article);
      } catch {
        showToast("Failed to remove tag", "error");
      }
    });
  });

  // Tag addition
  const tagInput = container.querySelector("#tag-input") as HTMLInputElement;
  const suggestionsEl = container.querySelector("#tag-suggestions") as HTMLElement;
  let debounceTimer: ReturnType<typeof setTimeout>;

  tagInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    const q = tagInput.value.trim();
    if (!q) {
      suggestionsEl.innerHTML = "";
      return;
    }
    debounceTimer = setTimeout(async () => {
      try {
        const result = await getTags(q);
        suggestionsEl.innerHTML = result.data
          .map((t) => `<div class="tag-suggestion" data-name="${escapeAttr(t.name)}">${escapeHtml(t.name)}</div>`)
          .join("");
        suggestionsEl.querySelectorAll(".tag-suggestion").forEach((el) => {
          el.addEventListener("click", () => addTag((el as HTMLElement).dataset.name!));
        });
      } catch {
        suggestionsEl.innerHTML = "";
      }
    }, 200);
  });

  tagInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      const name = tagInput.value.trim();
      if (name) addTag(name);
    }
  });

  async function addTag(name: string): Promise<void> {
    tagInput.value = "";
    suggestionsEl.innerHTML = "";
    try {
      const updated = await addTagToArticle(id, name);
      article.tags = updated.tags;
      renderArticle(id, article);
    } catch {
      showToast("Failed to add tag", "error");
    }
  }
}

function renderTags(tags: Tag[]): string {
  return tags
    .map(
      (t) =>
        `<span class="tag-chip">${escapeHtml(t.name)}<button class="tag-chip-remove" data-tag-id="${t.id}">&times;</button></span>`
    )
    .join("");
}

function escapeHtml(s: string): string {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

function escapeAttr(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
