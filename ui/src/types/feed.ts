export interface Feed {
  id: number;
  title: string;
  feed_url: string;
  site_url: string;
  source_type: string;
  created_at: string;
  last_fetched_at: string | null;
}
