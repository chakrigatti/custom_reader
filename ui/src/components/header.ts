import { syncAll } from "../services/sync-service";
import { showToast } from "./toast";

export interface HeaderCallbacks {
  onAddFeed: () => void;
  onNavigateHome: () => void;
  onSyncComplete: () => void;
}

export function mountHeader(el: HTMLElement, callbacks: HeaderCallbacks): void {
  el.innerHTML = `
    <div class="header-inner">
      <h1 class="header-title" tabindex="0">Reader</h1>
      <div class="header-actions">
        <button id="btn-sync" class="btn btn--secondary" title="Sync all feeds">Sync</button>
        <button id="btn-add-feed" class="btn btn--primary">+ Add Feed</button>
      </div>
    </div>
  `;

  el.querySelector(".header-title")!.addEventListener("click", callbacks.onNavigateHome);

  el.querySelector("#btn-add-feed")!.addEventListener("click", callbacks.onAddFeed);

  const syncBtn = el.querySelector("#btn-sync") as HTMLButtonElement;
  syncBtn.addEventListener("click", async () => {
    syncBtn.disabled = true;
    syncBtn.textContent = "Syncing...";
    try {
      const result = await syncAll();
      const total = result.data.reduce((sum, r) => sum + r.fetched, 0);
      showToast(`Synced ${total} new article${total !== 1 ? "s" : ""}`, "success");
      callbacks.onSyncComplete();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Sync failed", "error");
    } finally {
      syncBtn.disabled = false;
      syncBtn.textContent = "Sync";
    }
  });
}
