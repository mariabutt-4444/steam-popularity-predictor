import React, { useState } from 'react';
import {
  Sparkles,
  Lock,
  ArrowRight,
  Info,
  Sliders,
  Calendar,
  DollarSign,
  Tag,
  Monitor,
} from 'lucide-react';

export const PredictPlaceholderPage: React.FC = () => {
  const [price, setPrice] = useState<number>(14.99);
  const [releaseMonth, setReleaseMonth] = useState<number>(10);
  const [genre, setGenre] = useState<string>('Action;Indie');
  const [platforms, setPlatforms] = useState<string[]>(['windows']);

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Title & Badge */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-500/20 rounded-2xl">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-500/10 border border-amber-500/30 text-amber-500 rounded-full text-xs font-bold uppercase tracking-wider mb-2">
            <Lock className="w-3 h-3" /> Coming in Project 2
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-800 dark:text-white">
            Pre-Launch Popularity Tier Predictor
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-xl">
            This simulator form is fully designed to plug seamlessly into the upcoming{' '}
            <code className="text-amber-500 font-mono">/api/predict</code> endpoint (Stage 2: scikit-learn
            Pipeline with ColumnTransformer & GridSearchCV).
          </p>
        </div>
        <div className="text-right">
          <span className="text-xs font-mono bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-500">
            HTTP 501 Not Implemented
          </span>
        </div>
      </div>

      {/* Simulator Form (Disabled with aesthetic overlay) */}
      <div className="relative bg-white dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm p-8 space-y-6">
        {/* Architectural Note Box */}
        <div className="p-4 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 rounded-xl text-xs text-rose-800 dark:text-rose-300 flex items-start gap-3">
          <Info className="w-5 h-5 shrink-0 text-rose-500 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold">Zero Restructuring Guarantee:</p>
            <p>
              Pre-launch features (Price, Genres, Supported Platforms, Release Month, Age Rating,
              Achievements) are strictly isolated from post-launch outcomes (Ratings, Review Scores, Playtime).
              When Stage 2 is delivered, wiring this interface to the real ML model requires zero structural changes.
            </p>
          </div>
        </div>

        {/* Inputs */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 opacity-80">
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <DollarSign className="w-4 h-4 text-emerald-500" />
              Proposed Launch Price (USD)
            </label>
            <input
              type="number"
              step="0.01"
              value={price}
              disabled
              className="w-full px-4 py-2.5 text-sm bg-slate-100 dark:bg-slate-800/80 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-700 dark:text-slate-200 font-mono cursor-not-allowed"
            />
            <span className="text-[11px] text-slate-400 mt-1 block">
              Tested sweet spot: $0.00 (F2P) to $29.99
            </span>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Calendar className="w-4 h-4 text-rose-500" />
              Planned Release Month
            </label>
            <select
              value={releaseMonth}
              disabled
              className="w-full px-4 py-2.5 text-sm bg-slate-100 dark:bg-slate-800/80 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-700 dark:text-slate-200 cursor-not-allowed"
            >
              {[
                'January',
                'February',
                'March',
                'April',
                'May',
                'June',
                'July',
                'August',
                'September',
                'October',
                'November',
                'December',
              ].map((m, idx) => (
                <option key={m} value={idx + 1}>
                  {m}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Tag className="w-4 h-4 text-purple-500" />
              Primary Game Genres
            </label>
            <input
              type="text"
              value={genre}
              disabled
              className="w-full px-4 py-2.5 text-sm bg-slate-100 dark:bg-slate-800/80 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-700 dark:text-slate-200 cursor-not-allowed"
            />
            <span className="text-[11px] text-slate-400 mt-1 block">
              Multi-hot encoded via ColumnTransformer in Stage 2
            </span>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Monitor className="w-4 h-4 text-amber-500" />
              Target Platforms
            </label>
            <div className="flex gap-4 pt-2">
              <label className="flex items-center gap-2 text-xs font-medium text-slate-600 dark:text-slate-300">
                <input type="checkbox" checked disabled className="rounded text-rose-600" />
                Windows
              </label>
              <label className="flex items-center gap-2 text-xs font-medium text-slate-600 dark:text-slate-300">
                <input type="checkbox" checked disabled className="rounded text-rose-600" />
                macOS
              </label>
              <label className="flex items-center gap-2 text-xs font-medium text-slate-600 dark:text-slate-300">
                <input type="checkbox" checked disabled className="rounded text-rose-600" />
                Linux
              </label>
            </div>
            <span className="text-[11px] text-slate-400 mt-2 block">
              Cross-platform titles increase High tier probability by 2.5x
            </span>
          </div>
        </div>

        {/* Action Button */}
        <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex justify-between items-center">
          <div className="text-xs text-slate-500 flex items-center gap-1.5">
            <Sliders className="w-4 h-4 text-slate-400" />
            Class targets: Low (&le;20k), Medium (20k-200k), High (&gt;200k)
          </div>

          <button
            disabled
            className="px-6 py-3 bg-slate-300 dark:bg-slate-800 text-slate-500 dark:text-slate-400 rounded-xl text-xs font-bold cursor-not-allowed flex items-center gap-2 border border-slate-300 dark:border-slate-700"
          >
            <Lock className="w-4 h-4 text-amber-500" /> Run Inference (Coming in Stage 2)
          </button>
        </div>
      </div>
    </div>
  );
};
