from fastapi import FastAPI

from api.core.settings import settings
from api.v1.routers import auth_router, jobs_router

app = FastAPI(
    title="Plate Tracker API",
    version="1.0.0",
    openapi_url=f"{settings.api_prefix}/openapi.json",
)

app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(jobs_router, prefix=settings.api_prefix)


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
