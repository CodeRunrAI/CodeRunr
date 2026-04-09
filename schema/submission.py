from typing import Optional, List, Dict, Union, Annotated
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, AfterValidator


def validate_string_size_in_kb(v: str) -> str:
    MAX_SIZE_BYTES = 100 * 1024  # 100KB
    if len(v.encode("utf-8")) > MAX_SIZE_BYTES:
        raise ValueError(
            f"String size exceeds the maximum allowed of {MAX_SIZE_BYTES / 1024:.0f} KB"
        )
    return v


KbString = Annotated[str, AfterValidator(validate_string_size_in_kb)]


class SubmissionCreate(BaseModel):
    """Pydantic model to create new SubmissionRequest"""

    token: Optional[UUID] = None
    """Optional UUID token provided by client"""
    source_code: KbString
    """Source code that will be executed"""
    language_id: int
    """Valid language id"""
    stdin: Optional[KbString] = None
    """Optional stdin for program as input"""
    expected_output: Optional[KbString] = None
    """Expected output if or not stdin provided"""
    cpu_time_limit: float = Field(default=1, ge=0.1, le=15)
    """Max cpu time boundary to run the program, if exceeded, program will exited with non-zero status code"""
    cpu_extra_time: float = Field(default=1, ge=0, le=5)
    """Extra CPU time, a program can use"""
    wall_time_limit: float = Field(default=10, ge=0.5, le=30)
    """Wall time limit, this is for sleeping program, if program sleeps more than this required will exited"""
    memory_limit: int = Field(
        default=256 * 1024, ge=10 * 1024, le=512 * 1024, description="KB"
    )
    """Total max memory a program can use"""
    stack_limit: int = Field(
        default=64 * 1024, ge=10 * 1024, le=512 * 1024, description="KB"
    )
    """Total max stack memory a program can use"""
    max_file_size: int = Field(
        default=1 * 1024, ge=1 * 1024, le=20 * 1024, description="KB"
    )
    """Maximum file that a program can create"""
    max_processes_and_or_threads: int = Field(default=64, ge=1, le=128)
    """How many processes or threads a program can create"""
    limit_per_process_and_thread_cpu_time_usages: bool = False
    """If true, then each process or thread can utilize cpu_time_limit individually"""
    limit_per_process_and_thread_memory_usages: bool = False
    """If true, then each process or thread can utilize memory_limit individually"""
    webhook_url: Optional[HttpUrl] = None
    """Optional webhook url to post the submission data"""


class SubmissionBatchCreate(BaseModel):
    """Pydantic model to store the list of `SubmissionCreate`"""

    submissions: list[SubmissionCreate] = Field(..., min_length=1, max_length=20)
    """A list of submissionCreate"""


class SubmissionResponse(BaseModel):
    """Pydantic model to create SubmissionResponse"""

    token: UUID
    source_code: str
    language_id: int
    stdin: Optional[str] = None
    expected_output: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None
    message: Optional[str] = None
    status: str
    time: Optional[float] = None
    wall_time: Optional[float] = None
    memory: Optional[int] = None
    exit_code: Optional[int] = None
    exit_signal: Optional[int] = None
    cpu_time_limit: float
    cpu_extra_time: float
    wall_time_limit: float
    memory_limit: int
    stack_limit: int
    max_file_size: int
    max_processes_and_or_threads: int
    limit_per_process_and_thread_cpu_time_usages: bool
    limit_per_process_and_thread_memory_usages: bool
    webhook_url: Optional[HttpUrl] = None
    created_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    model_config = {"from_attributes": True, "extra": "ignore"}


class SubmissionBatchResponse(BaseModel):
    """Pydantic model to create SubmissionBatchResponse"""

    token: UUID
    submissions: List[Union[SubmissionResponse, Dict[str, str]]]

    model_config = {"from_attributes": True, "extra": "ignore"}
