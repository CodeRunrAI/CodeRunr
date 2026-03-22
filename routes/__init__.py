from fastapi import APIRouter, Depends

from config import settings
from .submissions import router as submissions_router
from .languages import router as languages_router
from utils.security import require_api_key

api_router = APIRouter(prefix=settings.API_V1_STR)


@api_router.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}


api_router.include_router(languages_router, dependencies=[Depends(require_api_key)])
api_router.include_router(submissions_router, dependencies=[Depends(require_api_key)])

__all__ = ["api_router"]
