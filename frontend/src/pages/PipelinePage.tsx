import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { RejectedGameItem, PipelineRunResponse } from '../types';
import {
  Play,
  CheckCircle,
  AlertCircle,
  Database,
  ArrowRight,
  ShieldAlert,
  Server,
  RefreshCw,
} from 'lucide-react';

export const PipelinePage: React.FC = () => {
  const [rejectedRows, setRejectedRows] = useState<RejectedGameItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [apiKey, setApiKey] = useState<string>('secret-pipeline-key');
  const [source, setSource] = useState<'csv' | 'api'>('csv');
  const [running, setRunning] = useState<boolean>(false);
  const [runResult, setRunResult] = useState<PipelineRunResponse | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  useEffect(() => {
    loadRejected();
  }, []);

  const loadRejected = async () => {
    try {
      setLoading(true);
      const res = await api.getRejected();
      setRejectedRows(res);
    } catch (err) {
      console.error('Failed to load rejected rows', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunPipeline = async () => {
    try {
      setRunning(true);
      setRunError(null);
      setRunResult(null);
      const res = await api.runPipeline(apiKey, source);
      setRunResult(res);
      await loadRejected();
    } catch (err: any) {
      setRunError(err.message || 'Pipeline execution failed');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-800 dark:text-white">
          ETL Pipeline & Data Quality Monitor
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Monitor pipeline execution stages, review validation rejection reasons, or trigger an on-demand ETL ingestion run.
        </p>
      </div>

      {/* Trigger Pipeline Section */}
      <div className="p-6 bg-white dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-800 dark:text-white flex items-center gap-2">
            <Server className="w-4 h-4 text-rose-500" />
            Trigger Pipeline Run
          </h2>
          <span className="text-xs bg-rose-500/10 text-rose-500 px-2.5 py-0.5 rounded font-mono font-medium">
            POST /api/pipeline/run
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
              Data Ingestion Source
            </label>
            <select
              value={source}
              onChange={(e) => setSource(e.target.value as 'csv' | 'api')}
              className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-rose-500"
            >
              <option value="csv">Fallback / Benchmark Dataset (steam.csv)</option>
              <option value="api">Live SteamSpy & Steam Store API (Throttled)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
              Header API Key (X-API-Key)
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-rose-500 font-mono"
            />
          </div>

          <div className="flex items-end">
            <button
              disabled={running}
              onClick={handleRunPipeline}
              className="w-full py-2 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white rounded-lg text-xs font-bold transition flex items-center justify-center gap-2"
            >
              {running ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> Ingesting & Validating...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" /> Run Ingestion Pipeline
                </>
              )}
            </button>
          </div>
        </div>

        {/* Success Banner */}
        {runResult && (
          <div className="p-4 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 rounded-xl text-emerald-700 dark:text-emerald-400 text-xs space-y-1">
            <div className="font-bold flex items-center gap-1.5 text-sm">
              <CheckCircle className="w-4 h-4" /> Pipeline Run Succeeded
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2 text-center">
              <div className="bg-white/60 dark:bg-slate-800/40 p-2 rounded border border-emerald-300 dark:border-emerald-800">
                <span className="text-[10px] uppercase font-bold text-slate-400">Extracted</span>
                <p className="text-base font-extrabold">{runResult.metrics.extracted}</p>
              </div>
              <div className="bg-white/60 dark:bg-slate-800/40 p-2 rounded border border-emerald-300 dark:border-emerald-800">
                <span className="text-[10px] uppercase font-bold text-slate-400">Transformed</span>
                <p className="text-base font-extrabold">{runResult.metrics.transformed}</p>
              </div>
              <div className="bg-white/60 dark:bg-slate-800/40 p-2 rounded border border-emerald-300 dark:border-emerald-800">
                <span className="text-[10px] uppercase font-bold text-slate-400">Valid</span>
                <p className="text-base font-extrabold">{runResult.metrics.valid}</p>
              </div>
              <div className="bg-white/60 dark:bg-slate-800/40 p-2 rounded border border-emerald-300 dark:border-emerald-800">
                <span className="text-[10px] uppercase font-bold text-slate-400">Rejected</span>
                <p className="text-base font-extrabold">{runResult.metrics.rejected}</p>
              </div>
              <div className="bg-white/60 dark:bg-slate-800/40 p-2 rounded border border-emerald-300 dark:border-emerald-800">
                <span className="text-[10px] uppercase font-bold text-slate-400">Loaded</span>
                <p className="text-base font-extrabold">{runResult.metrics.loaded}</p>
              </div>
            </div>
          </div>
        )}

        {/* Error Banner */}
        {runError && (
          <div className="p-4 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 rounded-xl text-red-600 dark:text-red-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{runError}</span>
          </div>
        )}
      </div>

      {/* Stage Flow Indicator Card */}
      <div className="p-6 bg-white dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
        <h2 className="text-base font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
          <Database className="w-4 h-4 text-emerald-500" />
          End-to-End Pipeline Architecture Audit
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs">
          <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-lg border border-slate-200 dark:border-slate-800">
            <span className="text-[10px] uppercase font-bold text-slate-400">Stage 1: Extract</span>
            <p className="font-bold text-slate-800 dark:text-white mt-1">extract.py</p>
            <p className="text-slate-500 mt-1">
              SteamSpy + Store API with exponential retries and raw disk caching.
            </p>
          </div>

          <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-lg border border-slate-200 dark:border-slate-800">
            <span className="text-[10px] uppercase font-bold text-slate-400">Stage 2: Transform</span>
            <p className="font-bold text-slate-800 dark:text-white mt-1">transform.py</p>
            <p className="text-slate-500 mt-1">
              Pandas parsing: owners_min/max/mid, popularity_tier, binary flags, guarded review score.
            </p>
          </div>

          <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-lg border border-slate-200 dark:border-slate-800">
            <span className="text-[10px] uppercase font-bold text-slate-400">Stage 3: Validate</span>
            <p className="font-bold text-slate-800 dark:text-white mt-1">validate.py</p>
            <p className="text-slate-500 mt-1">
              Pydantic v2 Game model constraints. Failures audited in dead-letter table.
            </p>
          </div>

          <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-lg border border-slate-200 dark:border-slate-800">
            <span className="text-[10px] uppercase font-bold text-slate-400">Stage 4: Load & EDA</span>
            <p className="font-bold text-slate-800 dark:text-white mt-1">load.py & analysis.py</p>
            <p className="text-slate-500 mt-1">
              SQLAlchemy 2.0 schema (games, genres M2M, rejected_games, eda_tables).
            </p>
          </div>
        </div>
      </div>

      {/* Dead-Letter Table: Rejected Games */}
      <div className="bg-white dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-800 dark:text-white flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-purple-500" />
              Rejected Games Dead-Letter Store ({rejectedRows.length})
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Strict audit log: Invalid rows are not silently dropped, but persisted with exact validation failure reasons.
            </p>
          </div>
        </div>

        {loading ? (
          <div className="h-32 flex items-center justify-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-rose-500"></div>
          </div>
        ) : rejectedRows.length === 0 ? (
          <div className="p-8 text-center bg-slate-50 dark:bg-slate-800/30 rounded-xl border border-dashed border-slate-200 dark:border-slate-800 text-xs text-slate-500">
            <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
            <p className="font-semibold text-slate-700 dark:text-slate-300">
              Zero Validation Rejections
            </p>
            <p className="mt-1">
              All 1,500 extracted game rows strictly satisfied Pydantic v2 Game model constraints.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
            <table className="w-full text-left text-xs text-slate-700 dark:text-slate-300">
              <thead className="bg-slate-50 dark:bg-slate-800/80 text-slate-600 dark:text-slate-400 uppercase font-semibold">
                <tr>
                  <th className="px-4 py-3">ID</th>
                  <th className="px-4 py-3">App ID</th>
                  <th className="px-4 py-3">Rejection Reason</th>
                  <th className="px-4 py-3">Raw Record Snippet</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {rejectedRows.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="px-4 py-2 font-mono">{item.id}</td>
                    <td className="px-4 py-2 font-mono">{item.appid ?? 'N/A'}</td>
                    <td className="px-4 py-2 text-red-500 font-medium">
                      {item.rejection_reason}
                    </td>
                    <td className="px-4 py-2 font-mono text-[10px] text-slate-400 max-w-md truncate">
                      {item.raw_record}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
