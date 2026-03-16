type ToastVariant = "success" | "error" | "info";

export function showToast(message: string, variant: ToastVariant = "info"): void {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const el = document.createElement("div");
  el.className = `toast toast--${variant}`;
  el.textContent = message;
  container.appendChild(el);

  // Trigger entrance animation on next frame
  requestAnimationFrame(() => el.classList.add("toast--visible"));

  setTimeout(() => {
    el.classList.remove("toast--visible");
    el.addEventListener("transitionend", () => el.remove());
  }, 4000);
}
