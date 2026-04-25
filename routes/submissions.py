"""
Submission API routes.
"""

from uuid import UUID
from typing import Dict, List, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_async_db
from db.models.submission import SubmissionStatus
from db.repository.submissions import (
    create_submission,
    get_submission_by_token,
    get_submissions,
    delete_submission,
    create_submission_batch,
    get_submission_batch_by_token,
)
from schema import (
    APIResponse,
    SubmissionCreate,
    SubmissionResponse,
    SubmissionBatchCreate,
    SubmissionBatchResponse,
)
from worker.tasks import submit_submission_task


router = APIRouter(prefix="/submissions", tags=["Submissions"])


@router.post("", response_model=APIResponse[Dict[str, str]], status_code=201)
async def create_submission_endpoint(
    body: SubmissionCreate,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create a new code execution submission and enqueue it for processing.
    
    This endpoint accepts source code and environment details, stores them,
    and enqueues an asynchronous task to execute the code.
    
    ### Request Body: `SubmissionCreate`
    - `token` (UUID, optional): Optional UUID token provided by the client.
    - `source_code` (str): Source code to execute. Max 100KB.
    - `language_id` (int): Valid language ID.
    - `stdin` (str, optional): Optional standard input data.
    - `expected_output` (str, optional): Expected standard output data for comparison.
    - `cpu_time_limit` (float): Max CPU time (seconds) to run the program. Default 1.0 (Max 15.0).
    - `cpu_extra_time` (float): Extra CPU time a program can use. Default 1.0 (Max 5.0).
    - `wall_time_limit` (float): Wall time limit (seconds) for sleeping programs. Default 10.0 (Max 30.0).
    - `memory_limit` (int): Max Memory usage. Default 262144 KB (256MB) (Max 524288 KB).
    - `stack_limit` (int): Total max stack memory a program can use. Default 65536 KB (64MB).
    - `max_file_size` (int): Maximum file size that a program can create. Default 1024 KB.
    - `max_processes_and_or_threads` (int): How many processes or threads a program can create. Default 64 (Max 128).
    - `limit_per_process_and_thread_cpu_time_usages` (bool): If true, each process or thread can utilize the CPU time limit individually. Default False.
    - `limit_per_process_and_thread_memory_usages` (bool): If true, each process or thread can utilize the memory limit individually. Default False.
    - `webhook_url` (url, optional): Optional webhook URL for callback upon completion.
    
    ### Response (201 Created)
    Returns an `APIResponse` with the newly generated `token` and `status`.
    - `token`: Unique UUID for the submission.
    - `status`: Initial status (e.g., "queued").
    """
    submission = await create_submission(db, body)
    submit_submission_task.delay(str(submission.token))
    submission_response = {"token": str(submission.token), "status": submission.status}
    return APIResponse[Dict[str, str]](
        message="Submission Created", data=submission_response
    )


@router.get("", response_model=APIResponse[List[SubmissionResponse]])
async def get_submissions_endpoint(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
):
    """
    List submissions with pagination.
    
    Retrieve a paginated list of code execution submissions.
    
    ### Request Query Parameters
    - **`page`** (int): Page number (default is 1).
    - **`per_page`** (int): Number of items per page (default is 20, max is 100).
    
    ### Response
    Returns an `APIResponse` containing a list of `SubmissionResponse` objects.
    Each object contains full execution details including:
    `token`, `status`, `stdout`, `stderr`, `compile_output`, `time`, `memory`, `exit_code`, etc.
    """
    submissions_list = await get_submissions(db, page=page, per_page=per_page)
    submission_response_list = [
        SubmissionResponse.model_validate(submission) for submission in submissions_list
    ]
    return APIResponse[List[SubmissionResponse]](
        message="All Submissions", data=submission_response_list
    )


@router.post(
    "/batch",
    response_model=APIResponse[SubmissionBatchResponse],
    status_code=201,
)
async def create_submission_batch_endpoint(
    body: SubmissionBatchCreate,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create a batch of submissions and enqueue them all for processing.
    
    This endpoint is useful for submitting multiple code execution tasks
    simultaneously. All submissions will be grouped under a single batch token.
    
    ### Request Body: `SubmissionBatchCreate`
    - `submissions`: A list of 1 to 20 `SubmissionCreate` objects. Each object contains:
        - `token` (UUID, optional): Client-provided token.
        - `source_code` (str): Source code to execute. Max 100KB.
        - `language_id` (int): Valid language ID.
        - `stdin` (str, optional): Standard input data.
        - `expected_output` (str, optional): Expected standard output.
        - `cpu_time_limit` (float, default 1.0): Max CPU time (seconds).
        - `cpu_extra_time` (float, default 1.0): Extra CPU time.
        - `wall_time_limit` (float, default 10.0): Wall time limit.
        - `memory_limit` (int, default 262144): Max Memory (KB).
        - `stack_limit` (int, default 65536): Max stack memory (KB).
        - `max_file_size` (int, default 1024): Max created file size (KB).
        - `max_processes_and_or_threads` (int, default 64): Max processes/threads.
        - `limit_per_process_and_thread_cpu_time_usages` (bool, default False)
        - `limit_per_process_and_thread_memory_usages` (bool, default False)
        - `webhook_url` (url, optional): Webhook URL.
    
    ### Response (201 Created)
    Returns an `APIResponse` containing a `SubmissionBatchResponse` object.
    - `token`: A unique UUID representing the whole batch.
    - `submissions`: A list of dictionaries containing individual `token` and `status` mappings for each submission.
    """
    batch = await create_submission_batch(db, body.submissions)
    for submission in batch.submissions:
        submit_submission_task.delay(str(submission.token))

    submission_response = SubmissionBatchResponse(
        token=batch.token,
        submissions=[
            {"token": str(submission.token), "status": submission.status}
            for submission in batch.submissions
        ],
    )
    return APIResponse[SubmissionBatchResponse](
        message="Submission batch created", data=submission_response
    )


@router.get("/batch/{token}", response_model=APIResponse[SubmissionBatchResponse])
async def get_submission_batch_endpoint(
    token: UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Retrieve a submission batch and all its individual submissions.
    
    ### Request Path Parameters
    - **`token`** (UUID): The unique UUID of the submission batch.
    
    ### Response
    Returns an `APIResponse` containing a `SubmissionBatchResponse` object.
    - `token`: The overall batch UUID.
    - `submissions`: A list of submission details.
      - If a submission is "queued" or "process", it returns just `{"token": ..., "status": ...}`.
      - If it is finalized, it returns the full `SubmissionResponse` with `stdout`, `exit_code`, `time`, `memory`, etc.
      
    **Errors:**
    - `404 Not Found`: If the batch token does not exist.
    """
    batch = await get_submission_batch_by_token(db, token)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    batch_submissions = []
    for submission in batch.submissions:
        if submission.status in [SubmissionStatus.queued, SubmissionStatus.process]:
            batch_submissions.append(
                {"token": str(submission.token), "status": submission.status}
            )
        else:
            batch_submissions.append(SubmissionResponse.model_validate(submission))

    submission_response = SubmissionBatchResponse(
        token=batch.token,
        submissions=batch_submissions,
    )
    return APIResponse[SubmissionBatchResponse](
        message="Submission batch data", data=submission_response
    )


@router.get(
    "/{token}", response_model=APIResponse[Union[SubmissionResponse, Dict[str, str]]]
)
async def get_submission_endpoint(
    token: UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Retrieve a specific submission by its token.
    
    Check the status and retrieve the output for a given code execution task.
    
    ### Request Path Parameters
    - **`token`** (UUID): The unique UUID of the individual submission.
    
    ### Response
    Returns an `APIResponse` with submission details.
    - If the task is still processing/queued, returns simple schema: `{"token": UUID, "status": str}`.
    - If finished, returns full `SubmissionResponse` including `stdout`, `stderr`, `time`, `memory`, `compile_output`, `exit_code`, etc.
    
    **Errors:**
    - `404 Not Found`: If the submission token does not exist.
    """
    submission = await get_submission_by_token(db, token)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if submission.status in [SubmissionStatus.queued, SubmissionStatus.process]:
        return APIResponse[Dict[str, str]](
            message="Submission data",
            data={"token": str(submission.token), "status": submission.status},
        )

    return APIResponse[SubmissionResponse](
        message="Submission data", data=SubmissionResponse.model_validate(submission)
    )


@router.delete("/{token}", response_model=APIResponse[None])
async def delete_submission_endpoint(
    token: UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Delete a submission by its token.
    
    Removes the specified submission record from the database.
    
    ### Request Path Parameters
    - **`token`** (UUID): The unique UUID of the specific submission.
    
    ### Response
    Returns an `APIResponse` with empty `data` confirming deletion.
    
    **Errors:**
    - `404 Not Found`: If the submission token does not exist.
    """
    deleted = await delete_submission(db, token)
    if not deleted:
        raise HTTPException(status_code=404, detail="Submission not found")
    return APIResponse[None](message="Submission Deleted")
