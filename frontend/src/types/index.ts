export interface GameListItem {
  appid: number;
  name: string;
  release_year: number;
  price: number;
  is_free: number;
  popularity_tier: 'Low' | 'Medium' | 'High';
  review_score: number;
  owners: string;
  genres?: string;
  platforms?: string;
}

export interface GameDetail extends GameListItem {
  release_date?: string;
  release_month: number;
  english: number;
  developer?: string;
  publisher?: string;
  required_age: number;
  achievements: number;
  is_windows: number;
  is_mac: number;
  is_linux: number;
  has_singleplayer: number;
  has_multiplayer: number;
  owners_min: number;
  owners_max: number;
  owners_mid: number;
  positive_ratings: number;
  negative_ratings: number;
  average_playtime: number;
  median_playtime: number;
  categories?: string;
  steamspy_tags?: string;
}

export interface PaginatedGames {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: GameListItem[];
}

export interface StatsIndexItem {
  table_name: string;
  insight: string;
}

export interface StatsTableResponse {
  table_name: string;
  insight: string;
  columns: string[];
  rows: (string | number)[][];
}

export interface RejectedGameItem {
  id: number;
  appid?: number;
  raw_record: string;
  rejection_reason: string;
  rejected_at?: string;
}

export interface PipelineRunResponse {
  status: string;
  metrics: {
    extracted: number;
    transformed: number;
    valid: number;
    rejected: number;
    loaded: number;
  };
}
