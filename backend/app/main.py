from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.routers.analytics import router as analytics_router
from app.routers.eta_prediction import router as eta_prediction_router
from app.routers.health import router as health_router
from app.routers.route_optimization import router as route_optimization_router
from app.routers.shipments import router as shipments_router
from app.services.eta_prediction import warm_eta_model_cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    warm_eta_model_cache()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(analytics_router, prefix=settings.api_prefix)
app.include_router(eta_prediction_router, prefix=settings.api_prefix)
app.include_router(route_optimization_router, prefix=settings.api_prefix)
app.include_router(shipments_router, prefix=settings.api_prefix)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "AI Logistics Control Tower API is running."}