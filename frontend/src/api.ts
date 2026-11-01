import {
  GameListItem,
  GameDetail,
  PaginatedGames,
  StatsIndexItem,
  StatsTableResponse,
  RejectedGameItem,
  PipelineRunResponse,
} from './types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API error (${res.status}): ${errorText || res.statusText}`);
  }
  return res.json();
}

export const api = {
  getHealth: () => fetchJson<{ status: string; service: string }>(`${API_BASE}/health`),

  getStatsIndex: () => fetchJson<StatsIndexItem[]>(`${API_BASE}/stats`),

  getStatsTable: (tableName: string) =>
    fetchJson<StatsTableResponse>(`${API_BASE}/stats/${tableName}`),

  getGames: (params: {
    search?: string;
    genre?: string;
    tier?: string;
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams();
    if (params.search) query.set('search', params.search);
    if (params.genre) query.set('genre', params.genre);
    if (params.tier) query.set('tier', params.tier);
    if (params.page) query.set('page', params.page.toString());
    if (params.page_size) query.set('page_size', params.page_size.toString());
    return fetchJson<PaginatedGames>(`${API_BASE}/games?${query.toString()}`);
  },

  getGameDetail: (appid: number) => fetchJson<GameDetail>(`${API_BASE}/games/${appid}`),

  getGenres: () => fetchJson<string[]>(`${API_BASE}/games/genres`),

  getRejected: () => fetchJson<RejectedGameItem[]>(`${API_BASE}/rejected`),

  runPipeline: (apiKey: string, source: 'csv' | 'api' = 'csv') =>
    fetchJson<PipelineRunResponse>(`${API_BASE}/pipeline/run?source=${source}`, {
      method: 'POST',
      headers: {
        'X-API-Key': apiKey,
      },
    }),
};
