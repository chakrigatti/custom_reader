import { createFeed } from "../services/feed-service";
import { ApiError } from "../types/api";
import { showToast } from "./toast";

export interface AddFeedFormCallbacks {
  onFeedAdded: () => void;
  onCancel: () => void;
}

export function mountAddFeedForm(parent: HTMLElement, callbacks: AddFeedFormCallbacks): void {
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.innerHTML = `
    <div class="modal">
      <h2 class="modal-title">Add Feed</h2>
      <form class="add-feed-form">
        <input type="url" class="input" name="url" placeholder="https://example.com/feed.xml" required autofocus />
        <div class="form-error" hidden></div>
        <div class="modal-actions">
          <button type="button" class="btn btn--secondary modal-cancel">Cancel</button>
          <button type="submit" class="btn btn--primary">Add</button>
        </div>
      </form>
    </div>
  `;

  parent.appendChild(overlay);

  const form = overlay.querySelector("form")!;
  const input = overlay.querySelector("input")! as HTMLInputElement;
  const errorEl = overlay.querySelector(".form-error")! as HTMLElement;
  const submitBtn = overlay.querySelector("[type=submit]") as HTMLButtonElement;

  function close(): void {
    overlay.remove();
  }

  overlay.querySelector(".modal-cancel")!.addEventListener("click", () => {
    close();
    callbacks.onCancel();
  });

  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) {
      close();
      callbacks.onCancel();
    }
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const url = input.value.trim();
    if (!url) return;

    errorEl.hidden = true;
    submitBtn.disabled = true;
    submitBtn.textContent = "Adding...";

    try {
      const feed = await createFeed(url);
      showToast(`Added "${feed.title}"`, "success");
      close();
      callbacks.onFeedAdded();
    } catch (err) {
      if (err instanceof ApiError) {
        errorEl.textContent = err.detail;
        errorEl.hidden = false;
      } else {
        showToast("Failed to add feed", "error");
        close();
      }
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Add";
    }
  });

  input.focus();
}
