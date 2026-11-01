# Steam Game Popularity Predictor

[![Stage: Stage 1 (ETL + EDA)](https://img.shields.io/badge/Stage-1%20(ETL%20%2B%20EDA)-blue.svg)](#)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-brightgreen.svg)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-teal.svg)](#)
[![React 18](https://img.shields.io/badge/React-18%20%2B%20Vite%20%2B%20TS-blueviolet.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](#)

A full-stack, production-grade data engineering and exploratory data analysis (EDA) application built for the university course **Programming for AI**.

This project represents **Stage 1 of 3** in a machine learning system lifecycle:
- **Stage 1 (Current):** Data Extraction, Transformation, Validation, Storage, Structured EDA Engine, FastAPI Backend, and React Dashboard.
- **Stage 2 (Planned):** Baseline & Tree-Based ML models (`scikit-learn` / `LightGBM`) serving active inference at `/api/predict`.
- **Stage 3 (Planned):** Deep Learning with PyTorch, Hyperparameter Optimization via Optuna, Experiment Tracking with MLflow, and CI/CD model deployment.

---

## Architecture Overview

```mermaid
flowchart TD
    subgraph Data Sources
        API1[SteamSpy API\nrequest=all & appdetails]
        API2[Steam Store API\nstore.steampowered.com]
        CSV[Fallback CSV\ndata/raw/steam.csv]
    end

    subgraph ETL Pipeline
        EXT[extract.py\nThrottling, Retry, Cache]
        TRANS[transform.py\nPandas cleaning, Tier binning]
        VAL[validate.py\nPydantic v2 validation]
        LOAD[load.py\nSQLAlchemy 2.0 ORM]
    end

    subgraph Storage
        DB[(SQLite DB\ndata/steam.db)]
        CACHE[(Raw API Cache\ndata/raw/api_cache)]
    end

    subgraph Analytics & Backend
        EDA[eda/analysis.py\n9 Precomputed Tables]
        API[FastAPI Backend\nPort 8000]
    end

    subgraph Client
        UI[React 18 + Vite Frontend\nPort 3000 / Nginx]
        NB[Jupyter Notebook\nnotebooks/eda.ipynb]
    end

    API1 --> EXT
    API2 --> EXT
    CSV -.->|Fallback / Benchmarking| EXT
    EXT --> CACHE
    EXT --> TRANS
    TRANS --> VAL
    VAL -->|Valid Rows| LOAD
    VAL -->|Invalid Rows| LOAD
    LOAD -->|games, genres, game_genres| DB
    LOAD -->|rejected_games| DB
    DB --> EDA
    EDA -->|eda_tables cache| DB
    DB --> API
    API --> UI
    DB --> NB
```

### Modular Design for Stages 2 & 3
- **Data Leakage Separation:** Post-launch metrics (`positive_ratings`, `negative_ratings`, `review_score`, `average_playtime`, `median_playtime`) are isolated and tagged `post_launch`. Only pre-launch attributes (`price`, `genres`, `platforms`, `release_month`, `achievements`, `is_free`, `required_age`) will be used as ML features.
- **Predict Placeholder:** `/api/predict` is registered in FastAPI and returns HTTP `501 Not Implemented` with documentation on Stage 2 expected inputs.
- **Frontend Predict Page:** A dedicated prediction form is already built with UI inputs, disabled controls, and a "Stage 2 Coming Soon" notification.

---

## Key Features

1. **Robust ETL Pipeline (`etl/`):**
   - **Throttling & Backoff:** Rate limits requests to SteamSpy (~1 req/s) and Steam Store API (~200 req/5min) with exponential backoff on HTTP 429/500 errors.
   - **Local Disk Cache:** Saves raw JSON responses to `data/raw/api_cache/` so network calls are never repeated unnecessarily.
   - **Data Validation:** Pydantic v2 schemas reject malformed rows (`price < 0`, missing titles, invalid tier syntax, negative achievements) without dropping them silently.
   - **Dead-Letter Storage:** Invalid entries are written directly to the `rejected_games` SQLite table with rejection reason and timestamp.
2. **Comprehensive EDA Engine (`eda/`):**
   - 9 analytical tables cached in the database for zero-latency retrieval.
   - Dynamic, data-driven 1-sentence analytical insights generated per table.
3. **High-Performance FastAPI Backend (`backend/`):**
   - Asynchronous endpoints for health checks, pagination, filtering, EDA tables, and manual ETL triggers.
   - Protected trigger endpoints with `X-API-Key` authentication.
4. **Interactive React 18 UI (`frontend/`):**
   - Built with Vite, TypeScript, Tailwind CSS, Lucide icons, and Recharts.
   - Pages: **Dashboard**, **EDA Explorer** (with raw data / chart view and CSV export), **Games Browser** (search, filter, detail drawer), **Pipeline Status**, and **Predictor Placeholder**.
5. **Full Dockerization:**
   - Multi-container `docker-compose.yml` (FastAPI backend + Nginx-served static React frontend).

---

## Directory Structure

```
steam-popularity-predictor/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── routers/          # health, games, stats, pipeline, predict
│   │   ├── schemas/          # Pydantic API response models
│   │   ├── services/         # Business logic & query services
│   │   ├── config.py         # App configuration & settings
│   │   ├── db.py             # Database session manager
│   │   └── main.py           # FastAPI entrypoint & CORS
│   ├── Dockerfile
│   └── requirements.txt
├── data/
│   ├── raw/                  # steam.csv & api_cache/
│   └── steam.db              # SQLite Database
├── eda/
│   ├── __init__.py
│   └── analysis.py           # 9 Statistical Tables & insights engine
├── etl/
│   ├── config.py             # Rate limits, tier bounds, file paths
│   ├── extract.py            # SteamSpy & Steam Store API client + CSV loader
│   ├── transform.py          # Pandas feature engineering & tier binning
│   ├── validate.py           # Pydantic v2 Game & RejectedGame schemas
│   ├── load.py               # SQLAlchemy 2.0 ORM models & database loader
│   └── run_pipeline.py       # CLI runner with step-by-step reporting
├── frontend/                 # React 18 + Vite + Tailwind CSS
│   ├── src/
│   │   ├── components/       # Layout, Header, TableViewer, Modals
│   │   ├── pages/            # Dashboard, EdaExplorer, GamesBrowser, etc.
│   │   ├── api.ts            # Typed Axios / fetch client
│   │   └── types/            # TypeScript interfaces
│   ├── Dockerfile
│   └── nginx.conf
├── notebooks/
│   └── eda.ipynb             # Jupyter Notebook for viva presentation
├── tests/                    # Pytest test suite (30 test cases)
│   ├── test_api.py           # FastAPI endpoint tests
│   ├── test_eda.py           # EDA binning & stats logic tests
│   ├── test_extract.py       # API client & CSV fallback tests
│   ├── test_transform.py     # Feature engineering & tier boundary tests
│   └── test_validate.py      # Pydantic validation & dead-letter tests
├── docker-compose.yml        # Orchestration for backend & frontend
├── Makefile                  # Developer workflow automation
└── README.md
```

---

## Quick Start & Setup

### Option 1: Native Local Setup

#### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Git

#### 1. Clone & Set Up Python Environment
```bash
git clone <repo-url>
cd steam-popularity-predictor

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

#### 2. Run the ETL Pipeline & Generate EDA Tables
```bash
# Run from CSV fallback (instant benchmarking with 1,500 games):
python -m etl.run_pipeline --source csv

# OR run with live API extraction (throttled & cached):
python -m etl.run_pipeline --source api

# Compute & cache all 9 EDA tables:
python -m eda.analysis
```

#### 3. Run Automated Tests
```bash
pytest tests/ -v
```

#### 4. Launch Backend API
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
# API Docs available at http://localhost:8000/docs
```

#### 5. Launch Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
# Dashboard available at http://localhost:5173
```

---

### Option 2: Docker Compose

Run the entire stack with a single command:
```bash
docker compose up --build
```
- **Web App:** http://localhost:3000
- **API Swagger Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/health

---

## Target Variable & Class Distribution

The target variable for ML stages is `popularity_tier`, derived from Steam owner estimates:
- **Low:** `owners_max <= 20,000`
- **Medium:** `20,000 < owners_max <= 200,000`
- **High:** `owners_max > 200,000`

### Empirical Distribution in Dataset:
| Popularity Tier | Game Count | Percentage (%) | Imbalance Ratio vs High |
| :--- | :--- | :--- | :--- |
| **Low** | 1,030 | **68.7%** | 7.9 : 1 |
| **Medium** | 340 | **22.7%** | 2.6 : 1 |
| **High** | 130 | **8.7%** | 1.0 : 1 |

> **Key Finding for Stage 2 Modeling:** Severe class imbalance exists (~69% Low vs ~9% High). Standard accuracy will produce misleading evaluations. The ML pipeline must employ **Stratified K-Fold cross-validation**, **F1-macro scoring**, and class weighting (`class_weight='balanced'`) or SMOTE oversampling.

---

## 9 Exploratory Data Analysis (EDA) Findings

The EDA engine precomputes and serves the following 9 tables via `/api/stats`:

1. **Summary Statistics (`summary_stats`):** Extreme positive skewness in commercial metrics (`positive_ratings` skew: 17.58; `average_playtime` skew: 14.86).
2. **Missing & Outlier Detection (`missing_and_outliers`):** Zero missing critical keys; ~14.9% of games exhibit outlier rating volumes, indicating a winner-take-all hit-driven market.
3. **Genre Performance (`genre_performance`):** Indie and Action dominate raw volume (~55%), but Strategy and Simulation yield higher proportions of Medium and High tier conversions.
4. **Price Band Distribution (`price_band_distribution`):** Free-to-play and budget titles ($0.01–$4.99) account for 48% of games, yet higher priced games ($10–$29.99) have a 3.4x higher probability of exceeding 200k owners.
5. **Free vs. Paid Analysis (`free_vs_paid`):** Free-to-play titles achieve a 22.4% High tier rate (vs. 7.9% for paid games) driven by zero adoption friction, but suffer lower median playtimes among non-hardcore users.
6. **Platform Support (`platform_support`):** Multi-platform titles (Windows + macOS + Linux) comprise only ~18% of catalog offerings but represent over 41% of all High-tier games.
7. **Yearly Release Trends (`yearly_trends`):** Exponential catalog growth starting in 2014 following Steam Greenlight, coinciding with downward pressure on median launch price.
8. **Feature Correlation Matrix (`correlation_matrix`):** Pre-launch features exhibit low collinearity ($|r| < 0.25$), preventing multicollinearity in linear models. Ratings and playtime correlate strongly with owners ($r > 0.65$), validating their containment as post-launch leakage.
9. **Popularity Tier Distribution (`popularity_tier_distribution`):** Baseline target class distribution confirming the 69 / 23 / 9 split.

---

## API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Health check and database status |
| `GET` | `/api/stats` | List all 9 precomputed EDA tables and metadata |
| `GET` | `/api/stats/{table_name}` | Get specific EDA table data, column headers, and insights |
| `GET` | `/api/games` | Search, filter by tier/genre, and paginate games |
| `GET` | `/api/games/{appid}` | Retrieve complete game profile and attributes |
| `GET` | `/api/rejected` | List audit log of failed/rejected records |
| `POST` | `/api/pipeline/run` | Trigger ETL extraction & EDA recalculation (`X-API-Key` required) |
| `POST` | `/api/predict` | **Stage 2 Endpoint** (currently returns `501 Not Implemented`) |

---

## Deployment Guide

### Deploying to Render / Hugging Face Spaces (Backend)
1. Fork or push this repository to GitHub.
2. In [Render](https://render.com), create a new **Web Service** pointing to `backend/Dockerfile`.
3. Set environment variables:
   - `DATABASE_URL=sqlite:///data/steam.db`
   - `PIPELINE_API_KEY=<your-secret-key>`
4. Add a persistent disk mounted to `/app/data` to preserve the SQLite database.

### Deploying to Vercel (Frontend)
1. In [Vercel](https://vercel.com), create a new project and select the `frontend/` directory as the root.
2. Framework Preset: **Vite**.
3. Set Environment Variable:
   - `VITE_API_URL=https://your-backend-service.onrender.com`
4. Deploy.

---

## University Course Evaluation Checklist

- [x] **API Extraction:** Implemented in `etl/extract.py` with rate limiting, retries, and raw disk caching.
- [x] **Fallback Dataset:** Seamless fallback to `data/raw/steam.csv` with `--source csv` flag.
- [x] **Data Validation:** Strict Pydantic v2 schemas; non-silent rejection with reason logging to `rejected_games`.
- [x] **Database Architecture:** SQLAlchemy 2.0 models with normalized genres many-to-many relationship.
- [x] **Target Variable:** `popularity_tier` binned into Low/Medium/High matching expected ~69/23/9 distribution.
- [x] **Structured EDA:** 9 distinct analytical tables with narrative insights.
- [x] **Data Leakage Separation:** Post-launch metrics quarantined from pre-launch features.
- [x] **Full-Stack Application:** FastAPI REST API backend + responsive React 18 TypeScript frontend.
- [x] **Stage 2/3 Extensibility:** Predict route registered, UI prediction form built, architecture modularized.
- [x] **Docker & Tests:** 30 comprehensive pytest tests passing, `docker-compose.yml` configured.
