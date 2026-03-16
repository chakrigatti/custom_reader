import type { Feed } from "../types/feed";
import { getFeeds } from "../services/feed-service";
import { deleteFeed } from "../services/feed-service";
import { showToast } from "./toast";

const BOOKMARK_FEED_ID = 1;

export interface SidebarCallbacks {
  onSelectFeed: (feedId: number | null) => void;
  onFeedDeleted: () => void;
}

let selectedFeedId: number | null = null;
let callbacks: SidebarCallbacks;
let container: HTMLElement;
let feeds: Feed[] = [];

export function mountSidebar(el: HTMLElement, cbs: SidebarCallbacks): void {
  container = el;
  callbacks = cbs;
  refresh();
}

export async function refresh(): Promise<void> {
  if (feeds.length === 0) {
    container.innerHTML = `<div class="loading">Loading feeds...</div>`;
  }
  try {
    const result = await getFeeds();
    feeds = result.data;
  } catch {
    feeds = [];
  }
  render();
}

export function setSelected(feedId: number | null): void {
  selectedFeedId = feedId;
  render();
}

function render(): void {
  const items = feeds.map((f) => {
    const active = f.id === selectedFeedId ? "sidebar-item--active" : "";
    const deleteBtn = f.id === BOOKMARK_FEED_ID
      ? ""
      : `<button class="sidebar-delete" data-id="${f.id}" title="Delete feed">&times;</button>`;
    return `<li class="sidebar-item ${active}" data-feed-id="${f.id}">
      <span class="sidebar-item-title">${escapeHtml(f.title)}</span>
      ${deleteBtn}
    </li>`;
  }).join("");

  const allActive = selectedFeedId === null ? "sidebar-item--active" : "";

  container.innerHTML = `
    <nav class="sidebar-nav">
      <ul class="sidebar-list">
        <li class="sidebar-item sidebar-item--all ${allActive}" data-feed-id="all">
          <span class="sidebar-item-title">All Feeds</span>
        </li>
        ${items}
      </ul>
    </nav>
  `;

  container.querySelectorAll(".sidebar-item").forEach((item) => {
    const el = item as HTMLElement;
    el.addEventListener("click", (e) => {
      if ((e.target as HTMLElement).classList.contains("sidebar-delete")) return;
      const raw = el.dataset.feedId!;
      const id = raw === "all" ? null : Number(raw);
      selectedFeedId = id;
      callbacks.onSelectFeed(id);
      render();
    });
  });

  container.querySelectorAll(".sidebar-delete").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const id = Number((btn as HTMLElement).dataset.id);
      const feed = feeds.find((f) => f.id === id);
      if (!confirm(`Delete feed "${feed?.title ?? id}"?`)) return;
      try {
        await deleteFeed(id);
        showToast("Feed deleted", "success");
        if (selectedFeedId === id) {
          selectedFeedId = null;
          callbacks.onSelectFeed(null);
        }
        callbacks.onFeedDeleted();
        await refresh();
      } catch (err) {
        showToast(err instanceof Error ? err.message : "Delete failed", "error");
      }
    });
  });
}

function escapeHtml(s: string): string {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}
