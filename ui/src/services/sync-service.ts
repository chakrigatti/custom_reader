import type { SyncAllResponse } from "../types/api";
import { api } from "./api-client";

export async function syncAll(): Promise<SyncAllResponse> {
  return api.post<SyncAllResponse>("/sync");
}
