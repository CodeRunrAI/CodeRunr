from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_async_db
from db.repository.languages import get_language, get_languages
from schema import APIResponse, LanguageResponse


router = APIRouter(prefix="/languages", tags=["Languages"])


@router.get("", response_model=APIResponse[List[LanguageResponse]])
async def get_languages_endpoint(
    db: AsyncSession = Depends(get_async_db),
):
    """Get all available languages"""
    languages = await get_languages(db)
    language_response_list = [
        LanguageResponse.model_validate(lang) for lang in languages
    ]
    return APIResponse[List[LanguageResponse]](
        message="All languages", data=language_response_list
    )


@router.get("/{language_id}", response_model=APIResponse[LanguageResponse])
async def get_language_endpoint(
    language_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """Get language"""
    row = await get_language(db, language_id)
    if not row:
        raise HTTPException(status_code=404, detail="Language not found")

    language_response = LanguageResponse.model_validate(row)
    return APIResponse[LanguageResponse](
        message="Language response", data=language_response
    )
