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
    """
    Retrieve a list of all programming languages supported by the sandbox.
    
    This endpoint returns all the languages configured in the system,
    including their unique identifiers and version information.
    
    ### Response
    Returns an `APIResponse` object containing a list of `LanguageResponse` dictionaries in the `data` field.
    
    **LanguageResponse Fields:**
    - `id`: Unique integer identifier.
    - `name`: Language name (e.g. Python, CPP).
    - `version`: Version of the language.
    - `compile_cmd`: Command used to compile.
    - `run_cmd`: Command used to run.
    - `source_file`: File name where code is placed.
    - `is_archived`: Boolean indicating if archived.
    """
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
    """
    Retrieve details for a specific programming language.
    
    ### Request Path Parameters
    - **`language_id`** (int): The unique integer identifier of the given language.
    
    ### Response
    Returns an `APIResponse` object containing a single `LanguageResponse` dictionary in the `data` field.
    
    **LanguageResponse Fields:**
    - `id`: Unique integer identifier.
    - `name`: Language name (e.g. Python, CPP).
    - `version`: Version of the language.
    - `compile_cmd`: Command used to compile.
    - `run_cmd`: Command used to run.
    - `source_file`: File name where code is placed.
    - `is_archived`: Boolean indicating if archived.
    
    **Errors:**
    - `404 Not Found`: If the language_id does not exist.
    """
    row = await get_language(db, language_id)
    if not row:
        raise HTTPException(status_code=404, detail="Language not found")

    language_response = LanguageResponse.model_validate(row)
    return APIResponse[LanguageResponse](
        message="Language response", data=language_response
    )
