from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.api.routes import data, download, status, upload
from src.core.logger import logger
from src.core.settings import settings
from src.db import async_engine, connect_db
from src.middlewares.middleware_info_req import InfoRequestMiddleWare


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up and connecting to the database...")

    yield

    logger.info("Shutting down and disconnecting from the database...")
    await async_engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Freight Invoice Data Extraction System",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(InfoRequestMiddleWare)

app.include_router(upload.router)
app.include_router(status.router)
app.include_router(data.router)
app.include_router(download.router)


@app.get("/")
async def root():
    return {"name": settings.app_name, "version": settings.app_version, "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
