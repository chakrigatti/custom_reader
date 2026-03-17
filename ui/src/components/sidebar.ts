import type { Feed, Category } from "../types/feed";
import { getFeeds } from "../services/feed-service";
import { deleteFeed } from "../services/feed-service";
import { getCategories, setFeedCategories, createCategory } from "../services/category-service";
import { showToast } from "./toast";

const BOOKMARK_FEED_ID = 1;

export interface SidebarCallbacks {
  onSelectFeed: (feedId: number | null) => void;
  onSelectCategory: (categoryId: number) => void;
  onFeedDeleted: () => void;
  onManageCategories: () => void;
}

let selectedFeedId: number | null = null;
let selectedCategoryId: number | null = null;
let callbacks: SidebarCallbacks;
let container: HTMLElement;
let feeds: Feed[] = [];
let categoryList: Category[] = [];
let openDropdownFeedId: number | null = null;

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
    const feedResult = await getFeeds();
    feeds = feedResult.data;
  } catch {
    feeds = [];
  }
  try {
    const catResult = await getCategories();
    categoryList = catResult.data;
  } catch {
    categoryList = [];
  }
  render();
}

export function setSelected(feedId: number | null): void {
  selectedFeedId = feedId;
  selectedCategoryId = null;
  render();
}

export function setSelectedCategory(categoryId: number | null): void {
  selectedCategoryId = categoryId;
  selectedFeedId = null;
  render();
}

function hashColor(s: string): string {
  let hash = 0;
  for (let i = 0; i < s.length; i++) {
    hash = s.charCodeAt(i) + ((hash << 5) - hash);
  }
  const h = Math.abs(hash) % 360;
  return `hsl(${h}, 55%, 50%)`;
}

function faviconHtml(feed: Feed): string {
  if (feed.favicon_url) {
    return `<img class="sidebar-favicon" src="${escapeAttr(feed.favicon_url)}" alt="" width="16" height="16" onerror="this.style.display='none';this.nextElementSibling.style.display='inline-flex'">
    <span class="sidebar-favicon sidebar-favicon--fallback" style="display:none;background:${hashColor(feed.title)}">${escapeHtml(feed.title.charAt(0).toUpperCase())}</span>`;
  }
  return `<span class="sidebar-favicon sidebar-favicon--fallback" style="background:${hashColor(feed.title)}">${escapeHtml(feed.title.charAt(0).toUpperCase())}</span>`;
}

function feedItemHtml(f: Feed, showCatBtn: boolean): string {
  const active = f.id === selectedFeedId ? "sidebar-item--active" : "";
  const isBookmark = f.id === BOOKMARK_FEED_ID;
  const actionBtns = isBookmark ? "" : `
    <button class="sidebar-cat-btn" data-feed-id="${f.id}" title="Set categories">&#9776;</button>
    <button class="sidebar-delete" data-id="${f.id}" title="Delete feed">&times;</button>`;
  const dropdown = (showCatBtn && openDropdownFeedId === f.id) ? categoryDropdownHtml(f) : "";
  return `<li class="sidebar-item ${active}" data-feed-id="${f.id}">
    ${faviconHtml(f)}
    <span class="sidebar-item-title">${escapeHtml(f.title)}</span>
    ${actionBtns}
    ${dropdown}
  </li>`;
}

function categoryDropdownHtml(feed: Feed): string {
  const feedCatIds = new Set((feed.categories || []).map((c) => c.id));
  const options = categoryList.map((cat) => {
    const checked = feedCatIds.has(cat.id) ? "checked" : "";
    return `<label class="sidebar-cat-option">
      <input type="checkbox" data-cat-id="${cat.id}" ${checked} />
      ${escapeHtml(cat.name)}
    </label>`;
  }).join("");
  return `<div class="sidebar-cat-dropdown" data-dropdown-feed="${feed.id}">
    ${options || `<div class="sidebar-cat-empty">No categories yet</div>`}
    <div class="sidebar-cat-new">
      <input type="text" class="sidebar-cat-new-input" placeholder="New category..." />
    </div>
  </div>`;
}

function render(): void {
  // Group feeds by category
  const categorized = new Map<number, Feed[]>();
  const uncategorized: Feed[] = [];

  for (const feed of feeds) {
    if (feed.categories && feed.categories.length > 0) {
      for (const cat of feed.categories) {
        if (!categorized.has(cat.id)) categorized.set(cat.id, []);
        categorized.get(cat.id)!.push(feed);
      }
    } else {
      uncategorized.push(feed);
    }
  }

  let categorySections = "";
  for (const cat of categoryList) {
    const catFeeds = categorized.get(cat.id) || [];
    if (catFeeds.length === 0) continue;
    const catActive = selectedCategoryId === cat.id ? "sidebar-category--active" : "";
    const feedItems = catFeeds.map((f) => feedItemHtml(f, true)).join("");

    categorySections += `
      <details class="sidebar-category ${catActive}" open>
        <summary class="sidebar-category-name" data-category-id="${cat.id}">${escapeHtml(cat.name)}</summary>
        <ul class="sidebar-list">${feedItems}</ul>
      </details>`;
  }

  const uncatItems = uncategorized.map((f) => feedItemHtml(f, true)).join("");

  const allActive = selectedFeedId === null && selectedCategoryId === null ? "sidebar-item--active" : "";

  container.innerHTML = `
    <nav class="sidebar-nav">
      <ul class="sidebar-list">
        <li class="sidebar-item sidebar-item--all ${allActive}" data-feed-id="all">
          <span class="sidebar-item-title">All Feeds</span>
        </li>
      </ul>
      ${categorySections}
      ${uncatItems ? `<ul class="sidebar-list sidebar-uncategorized">${uncatItems}</ul>` : ""}
      <div class="sidebar-footer">
        <button class="sidebar-manage-btn" id="manage-categories-btn">Manage Categories</button>
      </div>
    </nav>
  `;

  // Event: click on feed items
  container.querySelectorAll(".sidebar-item[data-feed-id]").forEach((item) => {
    const el = item as HTMLElement;
    el.addEventListener("click", (e) => {
      const target = e.target as HTMLElement;
      if (target.classList.contains("sidebar-delete") ||
          target.classList.contains("sidebar-cat-btn") ||
          target.closest(".sidebar-cat-dropdown")) return;
      const raw = el.dataset.feedId!;
      if (raw === "all") {
        selectedFeedId = null;
        selectedCategoryId = null;
        callbacks.onSelectFeed(null);
      } else {
        const id = Number(raw);
        selectedFeedId = id;
        selectedCategoryId = null;
        callbacks.onSelectFeed(id);
      }
      openDropdownFeedId = null;
      render();
    });
  });

  // Event: click on category name
  container.querySelectorAll(".sidebar-category-name").forEach((el) => {
    el.addEventListener("dblclick", () => {
      const catId = Number((el as HTMLElement).dataset.categoryId);
      selectedCategoryId = catId;
      selectedFeedId = null;
      callbacks.onSelectCategory(catId);
      render();
    });
  });

  // Event: delete feed
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

  // Event: category button (toggle dropdown)
  container.querySelectorAll(".sidebar-cat-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const feedId = Number((btn as HTMLElement).dataset.feedId);
      openDropdownFeedId = openDropdownFeedId === feedId ? null : feedId;
      render();
    });
  });

  // Event: category dropdown checkboxes
  container.querySelectorAll(".sidebar-cat-dropdown input[type=checkbox]").forEach((cb) => {
    cb.addEventListener("change", async (e) => {
      e.stopPropagation();
      const dropdown = (cb as HTMLElement).closest(".sidebar-cat-dropdown") as HTMLElement;
      const feedId = Number(dropdown.dataset.dropdownFeed);
      const feed = feeds.find((f) => f.id === feedId);
      if (!feed) return;

      // Gather all checked category IDs from the dropdown
      const checked: number[] = [];
      dropdown.querySelectorAll("input[type=checkbox]").forEach((box) => {
        if ((box as HTMLInputElement).checked) {
          checked.push(Number((box as HTMLElement).dataset.catId));
        }
      });

      try {
        await setFeedCategories(feedId, checked);
        await refresh();
      } catch (err) {
        showToast(err instanceof Error ? err.message : "Failed to update categories", "error");
      }
    });
  });

  // Event: new category input in dropdown
  container.querySelectorAll(".sidebar-cat-new-input").forEach((input) => {
    input.addEventListener("click", (e) => e.stopPropagation());
    input.addEventListener("keydown", async (e) => {
      if ((e as KeyboardEvent).key !== "Enter") return;
      e.stopPropagation();
      const inp = input as HTMLInputElement;
      const name = inp.value.trim();
      if (!name) return;

      const dropdown = inp.closest(".sidebar-cat-dropdown") as HTMLElement;
      const feedId = Number(dropdown.dataset.dropdownFeed);

      try {
        // Create category then assign it
        const newCat = await createCategory(name);

        const feed = feeds.find((f) => f.id === feedId);
        const existingIds = (feed?.categories || []).map((c) => c.id);
        await setFeedCategories(feedId, [...existingIds, newCat.id]);
        showToast(`Category "${name}" created`, "success");
        await refresh();
      } catch (err) {
        showToast(err instanceof Error ? err.message : "Failed to create category", "error");
      }
    });
  });

  // Event: manage categories button
  const manageBtn = container.querySelector("#manage-categories-btn");
  if (manageBtn) {
    manageBtn.addEventListener("click", () => callbacks.onManageCategories());
  }

  // Close dropdown on outside click
  function onDocClick(e: MouseEvent): void {
    if (openDropdownFeedId !== null && !container.querySelector(".sidebar-cat-dropdown")?.contains(e.target as Node) &&
        !(e.target as HTMLElement).classList.contains("sidebar-cat-btn")) {
      openDropdownFeedId = null;
      render();
      document.removeEventListener("click", onDocClick);
    }
  }
  if (openDropdownFeedId !== null) {
    document.addEventListener("click", onDocClick);
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
