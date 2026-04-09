from typing import Generic, TypeVar, TypeAlias, Literal, Optional
from pydantic import BaseModel

from .language import LanguageCreate, LanguageResponse
from .submission import (
    SubmissionCreate,
    SubmissionBatchCreate,
    SubmissionResponse,
    SubmissionBatchResponse,
)


T = TypeVar("T")
APIStatus: TypeAlias = Literal["Success", "Error"]


class APIResponse(BaseModel, Generic[T]):
    """API Response schema"""

    status: APIStatus = "Success"
    """Status of the API response either `Success` or `Error`"""
    message: str = "Request Success"
    """Response message"""
    data: Optional[T] = None
    """Data of any type"""


__all__ = [
    "APIResponse",
    "LanguageCreate",
    "LanguageResponse",
    "SubmissionCreate",
    "SubmissionBatchCreate",
    "SubmissionResponse",
    "SubmissionBatchResponse",
]
