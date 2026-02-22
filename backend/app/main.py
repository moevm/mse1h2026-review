from fastapi import FastAPI
from app.core.database import engine, Base
from app.api.routes import worker_router, admin_router

# Буит алембик
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Reviewer Admin API")

app.include_router(worker_router)
app.include_router(admin_router)
