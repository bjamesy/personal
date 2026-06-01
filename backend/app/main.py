from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import calendar, outbound_clicks, restaurant_interest_events, restaurant_recommendation_clicks, restaurants, scraper_runs, screenings, theatres
from app.database import async_session_factory
from app.ingestion.seed import seed_theatres
from app.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    async with async_session_factory() as session:
        await seed_theatres(session)
    yield


app = FastAPI(title="Toronto Film Tracker", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type"],
)

app.include_router(screenings.router)
app.include_router(theatres.router)
app.include_router(scraper_runs.router)
app.include_router(outbound_clicks.router)
app.include_router(restaurant_interest_events.router)
app.include_router(restaurants.router)
app.include_router(restaurant_recommendation_clicks.router)
app.include_router(calendar.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
