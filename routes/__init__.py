from fastapi import APIRouter

from config import settings
from .submissions import router as submissions_router
from .languages import router as languages_router

api_router = APIRouter(prefix=settings.API_V1_STR)


@api_router.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}


api_router.include_router(languages_router)
api_router.include_router(submissions_router)

__all__ = ["api_router"]
