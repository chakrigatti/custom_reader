export interface OPMLImportResult {
  imported: number;
  skipped: number;
  errors: string[];
}

export async function importOPML(file: File): Promise<OPMLImportResult> {
  const formData = new FormData();
  formData.append("file", file);
  const resp = await fetch("/opml/import", {
    method: "POST",
    body: formData,
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || "Import failed");
  }
  return resp.json();
}

export function exportOPML(): void {
  window.location.href = "/opml/export";
}
