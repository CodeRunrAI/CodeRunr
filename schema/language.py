from typing import Optional
from pydantic import BaseModel


class LanguageCreate(BaseModel):
    """Schema to create a new language"""

    name: str
    """Name of the language e.g CPP, Python, Java, etc."""
    version: Optional[str] = None
    """Version of the language"""
    compile_cmd: Optional[str] = None
    """Compile command to compile the program written in the same language"""
    run_cmd: str
    """Run command to run the program written in the same language"""
    source_file: str
    """Name of the source file where the code will be placed"""
    is_archived: bool = False
    """Make is archived or not"""


class LanguageResponse(BaseModel):
    id: int
    """Id (Primary key from database table)"""
    name: str
    version: Optional[str] = None
    compile_cmd: Optional[str] = None
    run_cmd: str
    source_file: str
    is_archived: bool = False

    model_config = {"from_attributes": True, "extra": "ignore"}
