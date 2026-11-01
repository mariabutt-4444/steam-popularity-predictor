import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { GameListItem, GameDetail, PaginatedGames } from '../types';
import {
  Search,
  Filter,
  X,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Tag,
  Monitor,
  Users,
  Star,
  DollarSign,
  Clock,
  Award,
} from 'lucide-react';

export const GamesBrowser: React.FC = () => {
  const [gamesData, setGamesData] = useState<PaginatedGames | null>(null);
  const [genres, setGenres] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters
  const [search, setSearch] = useState<string>('');
  const [selectedGenre, setSelectedGenre] = useState<string>('');
  const [selectedTier, setSelectedTier] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(15);

  // Detail Drawer
  const [selectedAppid, setSelectedAppid] = useState<number | null>(null);
  const [detailGame, setDetailGame] = useState<GameDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);

  useEffect(() => {
    async function loadGenres() {
      try {
        const list = await api.getGenres();
        setGenres(list);
      } catch (err) {
        console.error('Failed to load genres', err);
      }
    }
    loadGenres();
  }, []);

  useEffect(() => {
    async function fetchGames() {
      try {
        setLoading(true);
        const res = await api.getGames({
          search: search.trim() || undefined,
          genre: selectedGenre || undefined,
          tier: selectedTier || undefined,
          page,
          page_size: pageSize,
        });
        setGamesData(res);
      } catch (err) {
        console.error('Failed to load games', err);
      } finally {
        setLoading(false);
      }
    }
    fetchGames();
  }, [search, selectedGenre, selectedTier, page, pageSize]);

  // Handle drawer open
  const openDetail = async (appid: number) => {
    setSelectedAppid(appid);
    try {
      setDetailLoading(true);
      const detail = await api.getGameDetail(appid);
      setDetailGame(detail);
    } catch (err) {
      console.error('Failed to load game detail', err);
    } finally {
      setDetailLoading(false);
    }
  };

  const closeDetail = () => {
    setSelectedAppid(null);
    setDetailGame(null);
  };

  const getTierBadge = (tier: string) => {
    switch (tier) {
      case 'High':
        return 'bg-amber-500/10 text-amber-500 border-amber-500/20';
      case 'Medium':
        return 'bg-rose-500/10 text-rose-500 border-rose-500/20';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-800 dark:text-white">
          Games Catalog Browser
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Paginated exploration of validated games in the database with search and multi-criteria filters.
        </p>
      </div>

      {/* Filter Bar */}
      <div className="p-4 bg-white dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm flex flex-col md:flex-row gap-4 justify-between items-center">
        {/* Search Input */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search game, developer, publisher..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-rose-500"
          />
        </div>

        {/* Dropdowns */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {/* Genre select */}
          <select
            value={selectedGenre}
            onChange={(e) => {
              setSelectedGenre(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-rose-500"
          >
            <option value="">All Genres</option>
            {genres.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>

          {/* Tier select */}
          <select
            value={selectedTier}
            onChange={(e) => {
              setSelectedTier(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-rose-500"
          >
            <option value="">All Popularity Tiers</option>
            <option value="Low">Low (≤ 20,000)</option>
            <option value="Medium">Medium (20k - 200k)</option>
            <option value="High">High (&gt; 200,000)</option>
          </select>

          {/* Reset Filters */}
          {(search || selectedGenre || selectedTier) && (
            <button
              onClick={() => {
                setSearch('');
                setSelectedGenre('');
                setSelectedTier('');
                setPage(1);
              }}
              className="text-xs text-rose-500 hover:underline px-2 py-1"
            >
              Clear filters
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="h-96 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-rose-500"></div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700 dark:text-slate-300">
              <thead className="bg-slate-50 dark:bg-slate-800/80 text-slate-600 dark:text-slate-400 uppercase font-semibold border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="px-5 py-3">App ID</th>
                  <th className="px-5 py-3">Title</th>
                  <th className="px-5 py-3">Year</th>
                  <th className="px-5 py-3">Price</th>
                  <th className="px-5 py-3">Popularity Tier</th>
                  <th className="px-5 py-3">Estimated Owners</th>
                  <th className="px-5 py-3">Review Score</th>
                  <th className="px-5 py-3">Genres</th>
                  <th className="px-5 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                {gamesData && gamesData.items.length > 0 ? (
                  gamesData.items.map((game) => (
                    <tr
                      key={game.appid}
                      onClick={() => openDetail(game.appid)}
                      className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors cursor-pointer"
                    >
                      <td className="px-5 py-3.5 font-mono text-slate-400">#{game.appid}</td>
                      <td className="px-5 py-3.5 font-medium text-slate-800 dark:text-white max-w-xs truncate">
                        {game.name}
                      </td>
                      <td className="px-5 py-3.5 text-slate-500">{game.release_year || 'N/A'}</td>
                      <td className="px-5 py-3.5 font-medium">
                        {game.is_free ? (
                          <span className="text-emerald-600 dark:text-emerald-400 font-semibold">
                            Free
                          </span>
                        ) : (
                          `$${game.price.toFixed(2)}`
                        )}
                      </td>
                      <td className="px-5 py-3.5">
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${getTierBadge(
                            game.popularity_tier
                          )}`}
                        >
                          {game.popularity_tier}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 font-mono text-slate-500">{game.owners}</td>
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-1.5 font-medium">
                          <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                          <span>{(game.review_score * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5 text-slate-500 max-w-xs truncate">
                        {game.genres || 'N/A'}
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            openDetail(game.appid);
                          }}
                          className="px-2.5 py-1 text-xs text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded transition"
                        >
                          Inspect
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={9} className="px-5 py-12 text-center text-slate-400">
                      No games match your criteria
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {gamesData && gamesData.total_pages > 1 && (
          <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
            <div>
              Showing{' '}
              <span className="font-semibold text-slate-700 dark:text-slate-300">
                {(page - 1) * pageSize + 1}
              </span>{' '}
              to{' '}
              <span className="font-semibold text-slate-700 dark:text-slate-300">
                {Math.min(page * pageSize, gamesData.total)}
              </span>{' '}
              of{' '}
              <span className="font-semibold text-slate-700 dark:text-slate-300">
                {gamesData.total}
              </span>{' '}
              titles
            </div>

            <div className="flex items-center gap-1">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="p-1.5 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="px-2 font-medium text-slate-700 dark:text-slate-300">
                Page {page} of {gamesData.total_pages}
              </span>
              <button
                disabled={page >= gamesData.total_pages}
                onClick={() => setPage((p) => Math.min(gamesData.total_pages, p + 1))}
                className="p-1.5 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Detail Slide-Over Drawer */}
      {selectedAppid !== null && (
        <div className="fixed inset-0 z-50 bg-slate-800/50 backdrop-blur-xs flex justify-end">
          <div className="w-full max-w-lg bg-white dark:bg-slate-800 border-l border-slate-200 dark:border-slate-800 h-full p-6 overflow-y-auto space-y-6 shadow-2xl">
            {/* Drawer Header */}
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
              <div>
                <span className="text-xs font-mono text-slate-400">
                  AppID: {selectedAppid}
                </span>
                <h2 className="text-lg font-bold text-slate-800 dark:text-white mt-0.5">
                  {detailGame?.name || 'Loading Game...'}
                </h2>
              </div>
              <button
                onClick={closeDetail}
                className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-white rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {detailLoading || !detailGame ? (
              <div className="h-64 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-rose-500"></div>
              </div>
            ) : (
              <div className="space-y-6 text-xs">
                {/* Meta stats badges */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-lg">
                    <span className="text-slate-400 block text-[10px] uppercase font-bold">
                      Popularity Tier
                    </span>
                    <span
                      className={`inline-block mt-1 px-2.5 py-0.5 rounded-full text-xs font-bold border ${getTierBadge(
                        detailGame.popularity_tier
                      )}`}
                    >
                      {detailGame.popularity_tier}
                    </span>
                  </div>
                  <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-lg">
                    <span className="text-slate-400 block text-[10px] uppercase font-bold">
                      Price
                    </span>
                    <span className="text-sm font-bold text-slate-800 dark:text-white mt-1 block">
                      {detailGame.is_free ? 'Free to Play' : `$${detailGame.price.toFixed(2)}`}
                    </span>
                  </div>
                </div>

                {/* Pre-launch Model Features Section */}
                <div>
                  <h3 className="font-bold text-slate-800 dark:text-white uppercase tracking-wider text-[11px] mb-2.5 text-rose-500">
                    Pre-Launch Predictor Features (Stage 2/3 Inputs)
                  </h3>
                  <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2.5">
                    <div className="flex justify-between py-1 border-b border-slate-200/60 dark:border-slate-700/50">
                      <span className="text-slate-500">Release Date</span>
                      <span className="font-medium text-slate-800 dark:text-white">
                        {detailGame.release_date || 'N/A'} (Month: {detailGame.release_month})
                      </span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-200/60 dark:border-slate-700/50">
                      <span className="text-slate-500">Developer</span>
                      <span className="font-medium text-slate-800 dark:text-white">
                        {detailGame.developer || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-200/60 dark:border-slate-700/50">
                      <span className="text-slate-500">Publisher</span>
                      <span className="font-medium text-slate-800 dark:text-white">
                        {detailGame.publisher || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-200/60 dark:border-slate-700/50">
                      <span className="text-slate-500">Supported Platforms</span>
                      <span className="font-medium text-slate-800 dark:text-white">
                        {detailGame.platforms}
                      </span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-200/60 dark:border-slate-700/50">
                      <span className="text-slate-500">Required Age / Achievements</span>
                      <span className="font-medium text-slate-800 dark:text-white">
                        Age: {detailGame.required_age}+ | Achievements: {detailGame.achievements}
                      </span>
                    </div>
                    <div className="flex justify-between py-1">
                      <span className="text-slate-500">Genres</span>
                      <span className="font-medium text-slate-800 dark:text-white text-right max-w-xs">
                        {detailGame.genres || 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Post-launch Outcomes Warning Section */}
                <div>
                  <div className="flex items-center gap-1.5 text-amber-500 font-bold uppercase tracking-wider text-[11px] mb-2.5">
                    <Star className="w-3.5 h-3.5" />
                    Post-Launch Outcomes (Data Leakage - Excluded from ML)
                  </div>
                  <div className="bg-amber-500/5 border border-amber-500/20 p-4 rounded-xl space-y-2">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Estimated Owners</span>
                      <span className="font-mono font-bold text-slate-800 dark:text-white">
                        {detailGame.owners} (Mid: {detailGame.owners_mid.toLocaleString()})
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Ratings Ratio</span>
                      <span className="font-medium text-emerald-600 dark:text-emerald-400">
                        {detailGame.positive_ratings.toLocaleString()} 👍 /{' '}
                        {detailGame.negative_ratings.toLocaleString()} 👎 (
                        {(detailGame.review_score * 100).toFixed(1)}%)
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Average Forever Playtime</span>
                      <span className="font-medium text-slate-800 dark:text-white">
                        {detailGame.average_playtime} mins (Median: {detailGame.median_playtime}{' '}
                        mins)
                      </span>
                    </div>
                  </div>
                </div>

                {/* External Steam Store link */}
                <div className="pt-2">
                  <a
                    href={`https://store.steampowered.com/app/${detailGame.appid}`}
                    target="_blank"
                    rel="noreferrer"
                    className="w-full py-2.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-white rounded-lg text-center font-medium transition flex items-center justify-center gap-2"
                  >
                    Open on Steam Store <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
