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
    """Create a new submission and enqueue it for processing."""
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
    """List submissions with pagination."""
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
    """Create a batch of submissions and enqueue them all for processing."""
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
    """Retrieve a submission batch and all its submissions."""
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
    """Retrieve a submission by its token."""
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
    """Delete a submission by its token."""
    deleted = await delete_submission(db, token)
    if not deleted:
        raise HTTPException(status_code=404, detail="Submission not found")
    return APIResponse[None](message="Submission Deleted")
