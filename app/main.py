from fastapi import FastAPI
from app.routers import locations, cameras, events, analytics, vectors, extra

app = FastAPI(
    title="API RESTful de Videovigilancia Inteligente",
    version="1.0.0",
    description="Sistema para la gestión y analítica de metadatos de videovigilancia."
)

app.include_router(locations.router)
app.include_router(cameras.router)
app.include_router(events.router)
app.include_router(analytics.router)
app.include_router(analytics.public_router)
app.include_router(vectors.router)
app.include_router(extra.router)
app.include_router(extra.public_router)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "API de Videovigilancia activa"}