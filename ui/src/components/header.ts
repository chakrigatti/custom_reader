import { syncAll } from "../services/sync-service";
import { importOPML, exportOPML } from "../services/opml-service";
import { showToast } from "./toast";

export interface HeaderCallbacks {
  onAddFeed: () => void;
  onNavigateHome: () => void;
  onSyncComplete: () => void;
  onImportComplete: () => void;
}

export function mountHeader(el: HTMLElement, callbacks: HeaderCallbacks): void {
  el.innerHTML = `
    <div class="header-inner">
      <h1 class="header-title" tabindex="0">Reader</h1>
      <div class="header-actions">
        <button id="btn-import" class="btn btn--secondary" title="Import OPML">Import</button>
        <button id="btn-export" class="btn btn--secondary" title="Export OPML">Export</button>
        <button id="btn-sync" class="btn btn--secondary" title="Sync all feeds">Sync</button>
        <button id="btn-add-feed" class="btn btn--primary">+ Add Feed</button>
      </div>
      <input type="file" id="opml-file-input" accept=".opml,.xml" style="display:none">
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

  const fileInput = el.querySelector("#opml-file-input") as HTMLInputElement;
  const importBtn = el.querySelector("#btn-import") as HTMLButtonElement;

  importBtn.addEventListener("click", () => {
    fileInput.click();
  });

  fileInput.addEventListener("change", async () => {
    const file = fileInput.files?.[0];
    if (!file) return;
    importBtn.disabled = true;
    importBtn.textContent = "Importing...";
    try {
      const result = await importOPML(file);
      showToast(
        `Imported ${result.imported}, skipped ${result.skipped}${result.errors.length ? `, ${result.errors.length} errors` : ""}`,
        result.errors.length ? "info" : "success",
      );
      callbacks.onImportComplete();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Import failed", "error");
    } finally {
      importBtn.disabled = false;
      importBtn.textContent = "Import";
      fileInput.value = "";
    }
  });

  el.querySelector("#btn-export")!.addEventListener("click", () => {
    exportOPML();
  });
}
