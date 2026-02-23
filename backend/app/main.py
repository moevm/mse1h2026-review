from fastapi import FastAPI
from app.api.routes import worker_router, admin_router

app = FastAPI(title="AI Reviewer API (Mock Mode)")


app.include_router(worker_router)
app.include_router(admin_router)


@app.get("/")
def health_check():
    return {"status": "ok", "mode": "test"}