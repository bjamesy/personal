from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.api.routes import scraper_runs, screenings, theatres
from app.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    yield


app = FastAPI(title="Toronto Theatre Screening Aggregator", lifespan=lifespan)

app.include_router(screenings.router)
app.include_router(theatres.router)
app.include_router(scraper_runs.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
