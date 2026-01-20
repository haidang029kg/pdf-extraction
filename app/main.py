from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import data, download, status, upload
from app.config import settings
from app.db.session import init_db

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Freight Invoice Data Extraction System",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(status.router)
app.include_router(data.router)
app.include_router(download.router)


@app.on_event("startup")
async def startup_event():
    init_db()
    print(f"✅ {settings.app_name} v{settings.app_version} started")


@app.get("/")
async def root():
    return {"name": settings.app_name, "version": settings.app_version, "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
