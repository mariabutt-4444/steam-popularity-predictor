import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { StatsIndexItem, StatsTableResponse } from '../types';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';
import {
  Download,
  Search,
  Sparkles,
  BarChart2,
  Table as TableIcon,
  HelpCircle,
} from 'lucide-react';

export const EdaExplorer: React.FC = () => {
  const [tablesList, setTablesList] = useState<StatsIndexItem[]>([]);
  const [activeTable, setActiveTable] = useState<string>('summary_stats');
  const [currentTableData, setCurrentTableData] = useState<StatsTableResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [viewMode, setViewMode] = useState<'both' | 'table' | 'chart'>('both');

  useEffect(() => {
    async function loadIndex() {
      try {
        const list = await api.getStatsIndex();
        setTablesList(list);
        if (list.length > 0) {
          setActiveTable(list[0].table_name);
        }
      } catch (err) {
        console.error('Failed to load EDA tables list', err);
      }
    }
    loadIndex();
  }, []);

  useEffect(() => {
    if (!activeTable) return;
    async function loadTable() {
      try {
        setLoading(true);
        const data = await api.getStatsTable(activeTable);
        setCurrentTableData(data);
        setSearchTerm('');
      } catch (err) {
        console.error(`Failed to load ${activeTable}`, err);
      } finally {
        setLoading(false);
      }
    }
    loadTable();
  }, [activeTable]);

  const downloadCsv = () => {
    if (!currentTableData) return;
    const header = currentTableData.columns.join(',');
    const rows = currentTableData.rows.map((row) =>
      row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(',')
    );
    const csvContent = 'data:text/csv;charset=utf-8,' + [header, ...rows].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${currentTableData.table_name}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const filteredRows =
    currentTableData?.rows.filter((row) =>
      row.some((cell) =>
        String(cell).toLowerCase().includes(searchTerm.toLowerCase().trim())
      )
    ) || [];

  // Helper chart renderer based on activeTable
  const renderChart = () => {
    if (!currentTableData || currentTableData.rows.length === 0) return null;

    if (activeTable === 'genre_performance') {
      const chartData = currentTableData.rows.slice(0, 10).map((r) => ({
        genre: String(r[0]),
        avgOwners: Number(r[2]),
        reviewScore: Number(r[3]) * 100,
      }));
      return (
        <div className="h-72 my-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis dataKey="genre" stroke="#94a3b8" fontSize={11} interval={0} angle={-25} textAnchor="end" height={50} />
              <YAxis stroke="#94a3b8" fontSize={11} />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }} />
              <Bar dataKey="avgOwners" name="Avg Owners (Mid)" fill="#38bdf8" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      );
    }

    if (activeTable === 'price_band_distribution') {
      const chartData = currentTableData.rows.map((r) => ({
        band: String(r[0]),
        pctLow: Number(r[4]),
        pctMed: Number(r[5]),
        pctHigh: Number(r[6]),
      }));
      return (
        <div className="h-72 my-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis dataKey="band" stroke="#94a3b8" fontSize={12} />
              <YAxis stroke="#94a3b8" fontSize={12} unit="%" />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }} />
              <Legend wrapperStyle={{ paddingTop: 10 }} />
              <Bar dataKey="pctLow" name="Low Tier %" fill="#94a3b8" stackId="a" />
              <Bar dataKey="pctMed" name="Medium Tier %" fill="#38bdf8" stackId="a" />
              <Bar dataKey="pctHigh" name="High Tier %" fill="#f59e0b" stackId="a" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      );
    }

    if (activeTable === 'free_vs_paid') {
      const chartData = currentTableData.rows.map((r) => ({
        category: String(r[0]),
        avgOwners: Number(r[3]),
        medianOwners: Number(r[4]),
      }));
      return (
        <div className="h-72 my-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis dataKey="category" stroke="#94a3b8" fontSize={12} />
              <YAxis stroke="#94a3b8" fontSize={12} />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }} />
              <Legend wrapperStyle={{ paddingTop: 10 }} />
              <Bar dataKey="avgOwners" name="Avg Owners" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="medianOwners" name="Median Owners" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      );
    }

    if (activeTable === 'platform_support') {
      const chartData = currentTableData.rows.map((r) => ({
        platform: String(r[0]),
        games: Number(r[1]),
        pctHigh: Number(r[5]),
      }));
      return (
        <div className="h-72 my-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis dataKey="platform" stroke="#94a3b8" fontSize={11} interval={0} angle={-15} textAnchor="end" height={45} />
              <YAxis stroke="#94a3b8" fontSize={12} />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }} />
              <Bar dataKey="games" name="Total Titles" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      );
    }

    if (activeTable === 'yearly_trends') {
      const chartData = currentTableData.rows.map((r) => ({
        year: String(r[0]),
        games: Number(r[1]),
        avgPrice: Number(r[2]),
        pctFree: Number(r[3]),
      }));
      return (
        <div className="h-72 my-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis dataKey="year" stroke="#94a3b8" fontSize={11} />
              <YAxis stroke="#94a3b8" fontSize={11} />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }} />
              <Bar dataKey="games" name="Titles Released" fill="#06b6d4" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      );
    }

    if (activeTable === 'popularity_tier_distribution') {
      const chartData = currentTableData.rows.map((r) => ({
        tier: String(r[0]),
        count: Number(r[1]),
        pct: Number(r[2]),
      }));
      return (
        <div className="h-72 my-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis dataKey="tier" stroke="#94a3b8" fontSize={12} />
              <YAxis stroke="#94a3b8" fontSize={12} />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }} />
              <Bar dataKey="count" name="Games Count" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      );
    }

    // Default correlation heat-grid preview or summary
    return (
      <div className="p-4 bg-slate-50 dark:bg-slate-800/40 rounded-lg text-xs text-slate-500 text-center my-4">
        Visual representation ready in statistical table below.
      </div>
    );
  };

  const formatTableName = (name: string) => {
    return name
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <div className="space-y-6">
      {/* Header and Table Tabs */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-800 dark:text-white">
          Exploratory Data Analysis Explorer
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Explore all 9 structured EDA tables with auto-generated statistical insights and interactive visualizations.
        </p>

        {/* Horizontal Navigation Tabs */}
        <div className="flex gap-2 overflow-x-auto pb-2 pt-4 border-b border-slate-200 dark:border-slate-800 scrollbar-thin">
          {tablesList.map((tab) => (
            <button
              key={tab.table_name}
              onClick={() => setActiveTable(tab.table_name)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${activeTable === tab.table_name
                ? 'bg-rose-600 text-white shadow-sm'
                : 'bg-white dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700/60'
                }`}
            >
              {formatTableName(tab.table_name)}
            </button>
          ))}
        </div>
      </div>

      {/* Main EDA Content Container */}
      <div className="bg-white dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm p-6 space-y-6">
        {/* Insight Banner */}
        <div className="p-4 bg-gradient-to-r from-rose-500/10 via-rose-500/5 to-transparent border-l-4 border-rose-500 rounded-r-xl">
          <div className="flex items-start gap-3">
            <Sparkles className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-rose-600 dark:text-rose-400">
                Auto-Generated Finding
              </span>
              <p className="text-sm text-slate-800 dark:text-slate-200 font-medium mt-0.5">
                {currentTableData?.insight || 'Loading analysis insight...'}
              </p>
            </div>
          </div>
        </div>

        {/* Toolbar: Search, View Mode, Download CSV */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search table values..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-800 dark:text-white focus:outline-none focus:ring-1 focus:ring-rose-500"
            />
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
            <div className="flex bg-slate-100 dark:bg-slate-800 p-0.5 rounded-lg border border-slate-200 dark:border-slate-700">
              <button
                onClick={() => setViewMode('both')}
                className={`px-2.5 py-1 text-xs rounded-md transition ${viewMode === 'both'
                  ? 'bg-white dark:bg-slate-700 text-slate-800 dark:text-white shadow-xs font-semibold'
                  : 'text-slate-500 hover:text-slate-800 dark:hover:text-white'
                  }`}
              >
                All
              </button>
              <button
                onClick={() => setViewMode('chart')}
                className={`px-2.5 py-1 text-xs rounded-md transition flex items-center gap-1 ${viewMode === 'chart'
                  ? 'bg-white dark:bg-slate-700 text-slate-800 dark:text-white shadow-xs font-semibold'
                  : 'text-slate-500 hover:text-slate-800 dark:hover:text-white'
                  }`}
              >
                <BarChart2 className="w-3.5 h-3.5" /> Chart
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`px-2.5 py-1 text-xs rounded-md transition flex items-center gap-1 ${viewMode === 'table'
                  ? 'bg-white dark:bg-slate-700 text-slate-800 dark:text-white shadow-xs font-semibold'
                  : 'text-slate-500 hover:text-slate-800 dark:hover:text-white'
                  }`}
              >
                <TableIcon className="w-3.5 h-3.5" /> Table
              </button>
            </div>

            <button
              onClick={downloadCsv}
              className="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-medium rounded-lg border border-slate-200 dark:border-slate-700 transition flex items-center gap-1.5"
            >
              <Download className="w-3.5 h-3.5" /> Download CSV
            </button>
          </div>
        </div>

        {/* Loading Spinner */}
        {loading ? (
          <div className="h-64 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-rose-500"></div>
          </div>
        ) : (
          <>
            {/* Visual Chart Area */}
            {(viewMode === 'both' || viewMode === 'chart') && renderChart()}

            {/* Table Area */}
            {(viewMode === 'both' || viewMode === 'table') && (
              <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
                <table className="w-full text-left text-xs text-slate-700 dark:text-slate-300">
                  <thead className="bg-slate-50 dark:bg-slate-800/80 text-slate-600 dark:text-slate-400 uppercase font-semibold border-b border-slate-200 dark:border-slate-800">
                    <tr>
                      {currentTableData?.columns.map((col) => (
                        <th key={col} className="px-4 py-3 whitespace-nowrap">
                          {col.replace(/_/g, ' ')}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-mono">
                    {filteredRows.length > 0 ? (
                      filteredRows.map((row, idx) => (
                        <tr
                          key={idx}
                          className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
                        >
                          {row.map((cell, cIdx) => (
                            <td key={cIdx} className="px-4 py-2.5 whitespace-nowrap">
                              {typeof cell === 'number'
                                ? cell.toLocaleString(undefined, { maximumFractionDigits: 4 })
                                : String(cell)}
                            </td>
                          ))}
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td
                          colSpan={currentTableData?.columns.length || 1}
                          className="px-4 py-8 text-center text-slate-400 font-sans"
                        >
                          No matching records found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
