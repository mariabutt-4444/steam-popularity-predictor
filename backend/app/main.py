from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.routers import health, stats, games, pipeline, predict

app = FastAPI(
    title=settings.app_name,
    description="Steam Game Popularity Predictor - Stage 1 (ETL + EDA) REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
if not origins:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if "*" not in origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api
app.include_router(health.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(games.router, prefix="/api")
app.include_router(pipeline.router, prefix="/api")
app.include_router(predict.router, prefix="/api")

@app.get("/")
def root():
    return {
        "message": "Welcome to Steam Game Popularity Predictor API",
        "docs": "/docs",
        "health": "/api/health",
        "stats": "/api/stats",
        "games": "/api/games",
    }
