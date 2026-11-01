import React, { useState, useEffect } from 'react';
import { Dashboard } from './pages/Dashboard';
import { EdaExplorer } from './pages/EdaExplorer';
import { GamesBrowser } from './pages/GamesBrowser';
import { PipelinePage } from './pages/PipelinePage';
import { PredictPlaceholderPage } from './pages/PredictPlaceholderPage';
import {
  LayoutDashboard,
  BarChart3,
  Gamepad2,
  GitBranch,
  Sparkles,
  Sun,
  Moon,
  Database,
  ExternalLink,
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [darkMode, setDarkMode] = useState<boolean>(true);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'eda', label: 'EDA Explorer', icon: BarChart3 },
    { id: 'games', label: 'Games Browser', icon: Gamepad2 },
    { id: 'pipeline', label: 'ETL Pipeline', icon: GitBranch },
    { id: 'predict', label: 'Predict (Stage 2)', icon: Sparkles },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-[#0e141b] text-slate-800 dark:text-slate-100 font-sans transition-colors duration-200">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 bg-white/80 dark:bg-[#171a21]/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo & Project Title */}
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-rose-500 to-indigo-600 rounded-xl text-white shadow-sm shadow-rose-500/20">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <span className="font-extrabold text-sm tracking-tight text-slate-800 dark:text-white block leading-none">
                Steam Predictor
              </span>
              <span className="text-[10px] text-rose-600 dark:text-rose-400 font-semibold tracking-wider uppercase">
                Stage 1: ETL + EDA
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`px-3.5 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${isActive
                    ? 'bg-rose-50 dark:bg-rose-500/10 text-rose-600 dark:text-rose-400 font-bold'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/60'
                    }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Controls: Theme toggle & API Docs */}
          <div className="flex items-center gap-2">
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg border border-slate-200 dark:border-slate-700 transition"
            >
              OpenAPI Docs <ExternalLink className="w-3 h-3" />
            </a>

            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition"
              title="Toggle theme"
            >
              {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation bar */}
        <div className="md:hidden flex overflow-x-auto px-4 py-2 border-t border-slate-100 dark:border-slate-800/60 gap-1 scrollbar-none">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap flex items-center gap-1.5 ${isActive
                  ? 'bg-rose-600 text-white'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                  }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {item.label}
              </button>
            );
          })}
        </div>
      </header>

      {/* Main Page Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && <Dashboard onNavigate={(tab) => setActiveTab(tab)} />}
        {activeTab === 'eda' && <EdaExplorer />}
        {activeTab === 'games' && <GamesBrowser />}
        {activeTab === 'pipeline' && <PipelinePage />}
        {activeTab === 'predict' && <PredictPlaceholderPage />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 py-6 text-center text-xs text-slate-500 dark:text-slate-500">
        Steam Game Popularity Predictor &bull; Programming for AI &bull; Stage 1 of 3 (ETL + EDA)
      </footer>
    </div>
  );
}
