export interface Category {
  id: number;
  name: string;
  created_at: string;
}

export interface Feed {
  id: number;
  title: string;
  feed_url: string;
  site_url: string;
  source_type: string;
  favicon_url: string | null;
  created_at: string;
  last_fetched_at: string | null;
  categories: Category[];
}
