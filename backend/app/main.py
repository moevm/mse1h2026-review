from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import worker_router, admin_router
from app.core.database import engine, Base
import os


Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Reviewer API")

app.include_router(worker_router, prefix="/worker", tags=["Worker"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])

raw_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")

origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "ok"}