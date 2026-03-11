from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_async_db
from db.repository.languages import get_language, get_languages
from schema.language import LanguageResponse


router = APIRouter(prefix="/languages", tags=["Languages"])


@router.get("", response_model=list[LanguageResponse])
async def get_languages_endpoint(
    db: AsyncSession = Depends(get_async_db),
):
    rows = await get_languages(db)
    return [LanguageResponse.model_validate(r) for r in rows]


@router.get("/{language_id}", response_model=LanguageResponse)
async def get_language_endpoint(
    language_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    row = await get_language(db, language_id)
    if not row:
        raise HTTPException(status_code=404, detail="Language not found")
    return LanguageResponse.model_validate(row)
