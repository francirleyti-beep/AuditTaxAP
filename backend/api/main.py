from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter
import os

app = FastAPI(title="AuditTax AP API", version="2.0.0")

@app.on_event("startup")
async def startup():
    redis_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    r = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(r)

# CORS setup for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.api.routes import router
app.include_router(router, prefix="/api")

# Directories
UPLOAD_DIR = Path("uploads")
REPORTS_DIR = Path("reports")
UPLOAD_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

@app.get("/")
async def root():
    return {"message": "AuditTax AP API", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
