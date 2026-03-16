import { marked } from "marked";
import DOMPurify from "dompurify";

marked.setOptions({ breaks: true });

export function renderMarkdown(md: string): string {
  const raw = marked.parse(md);
  // marked.parse can return string | Promise<string>; with no async
  // extensions it always returns string synchronously.
  const html = typeof raw === "string" ? raw : "";
  return DOMPurify.sanitize(html);
}
