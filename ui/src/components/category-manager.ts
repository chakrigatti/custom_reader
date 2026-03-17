import type { Category } from "../types/feed";
import { getCategories, createCategory, renameCategory, deleteCategory } from "../services/category-service";
import { showToast } from "./toast";

export interface CategoryManagerCallbacks {
  onClose: () => void;
}

export function openCategoryManager(parent: HTMLElement, callbacks: CategoryManagerCallbacks): void {
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.id = "category-manager-overlay";
  parent.appendChild(overlay);

  let categories: Category[] = [];

  function close(): void {
    overlay.remove();
    callbacks.onClose();
  }

  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) close();
  });

  async function load(): Promise<void> {
    try {
      const result = await getCategories();
      categories = result.data;
    } catch {
      categories = [];
    }
    renderModal();
  }

  function renderModal(): void {
    const rows = categories.map((cat) => `
      <div class="catmgr-row" data-cat-id="${cat.id}">
        <input type="text" class="input catmgr-name" value="${escapeAttr(cat.name)}" data-cat-id="${cat.id}" />
        <button class="btn catmgr-delete" data-cat-id="${cat.id}" title="Delete">&times;</button>
      </div>
    `).join("");

    overlay.innerHTML = `
      <div class="modal catmgr-modal">
        <h2 class="modal-title">Manage Categories</h2>
        <div class="catmgr-add">
          <input type="text" class="input catmgr-add-input" placeholder="New category name..." />
          <button class="btn btn--primary catmgr-add-btn">Add</button>
        </div>
        <div class="catmgr-list">
          ${rows || `<div class="empty-state" style="padding:16px">No categories yet</div>`}
        </div>
        <div class="modal-actions">
          <button class="btn btn--secondary catmgr-close">Close</button>
        </div>
      </div>
    `;

    // Close button
    overlay.querySelector(".catmgr-close")!.addEventListener("click", close);

    // Add category
    const addInput = overlay.querySelector(".catmgr-add-input") as HTMLInputElement;
    const addBtn = overlay.querySelector(".catmgr-add-btn")!;

    async function doAdd(): Promise<void> {
      const name = addInput.value.trim();
      if (!name) return;
      try {
        await createCategory(name);
        showToast(`Category "${name}" created`, "success");
        await load();
      } catch (err) {
        showToast(err instanceof Error ? err.message : "Failed to create category", "error");
      }
    }

    addBtn.addEventListener("click", doAdd);
    addInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") doAdd();
    });

    // Rename on blur
    overlay.querySelectorAll(".catmgr-name").forEach((input) => {
      const inp = input as HTMLInputElement;
      const catId = Number(inp.dataset.catId);
      const original = inp.value;

      inp.addEventListener("blur", async () => {
        const newName = inp.value.trim();
        if (!newName || newName === original) {
          inp.value = original;
          return;
        }
        try {
          await renameCategory(catId, newName);
          showToast("Category renamed", "success");
          await load();
        } catch (err) {
          showToast(err instanceof Error ? err.message : "Rename failed", "error");
          inp.value = original;
        }
      });

      inp.addEventListener("keydown", (e) => {
        if (e.key === "Enter") inp.blur();
        if (e.key === "Escape") {
          inp.value = original;
          inp.blur();
        }
      });
    });

    // Delete
    overlay.querySelectorAll(".catmgr-delete").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const catId = Number((btn as HTMLElement).dataset.catId);
        const cat = categories.find((c) => c.id === catId);
        if (!confirm(`Delete category "${cat?.name ?? catId}"?`)) return;
        try {
          await deleteCategory(catId);
          showToast("Category deleted", "success");
          await load();
        } catch (err) {
          showToast(err instanceof Error ? err.message : "Delete failed", "error");
        }
      });
    });

    addInput.focus();
  }

  load();
}

function escapeAttr(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
