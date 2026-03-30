import uuid
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest
import worker.tasks as worker_tasks
from db.models import Language, Submission
from sandbox.schema import SandboxSubmission, SandboxSubmissionStatus
from sqlalchemy.orm import sessionmaker, Session


def _create_language(
    mock_language_sample: Dict[str, Any], sync_db: Session
) -> Language:
    language = Language(**mock_language_sample)
    sync_db.add(language)
    sync_db.commit()
    sync_db.refresh(language)
    return language


def _create_submission(
    mock_submission_sample: Dict[str, Any],
    sync_db: Session,
    *,
    token: uuid.UUID | None = None,
    language_id: int = 1,
    webhook_url: str | None = None,
) -> Submission:

    mock_submission_sample["token"] = uuid.UUID(mock_submission_sample["token"])
    if token:
        mock_submission_sample["token"] = token
    if language_id:
        mock_submission_sample["language_id"] = language_id
    if webhook_url:
        mock_submission_sample["webhook_url"] = webhook_url

    submission = Submission(**mock_submission_sample)
    sync_db.add(submission)
    sync_db.commit()
    sync_db.refresh(submission)
    return submission


class TestWorkerTasks:
    @pytest.fixture(autouse=True)
    def worker_session_local(self, sync_db: Session, monkeypatch: pytest.MonkeyPatch):
        testing_session_local = sessionmaker(
            bind=sync_db.bind,
            autoflush=False,
            autocommit=False,
        )
        monkeypatch.setattr(worker_tasks, "SyncSessionLocal", testing_session_local)
        return testing_session_local

    def test_submit_submission_task_failed_when_submission_is_missing(self):
        token = str(uuid.uuid4())
        result = worker_tasks.submit_submission_task(token)
        assert result == f"Submission failed {token}"

    def test_submit_submission_task_persists_sandbox_results(
        self,
        mock_language_sample: Dict[str, Any],
        mock_submission_sample: Dict[str, Any],
        sync_db: Session,
        monkeypatch: pytest.MonkeyPatch,
    ):
        _create_language(mock_language_sample, sync_db)
        submission = _create_submission(
            mock_submission_sample,
            sync_db,
            webhook_url="https://example.com/webhook",
        )
        post_data_on_callback = MagicMock()

        class FakeSandbox:
            def __init__(self, sandbox_submission: SandboxSubmission):
                self.submission = sandbox_submission

            def process_and_execute(self):
                self.submission.status = SandboxSubmissionStatus.acc
                self.submission.stdout = "hello\n"
                self.submission.stderr = ""
                self.submission.compile_output = None
                self.submission.time = 0.01
                self.submission.wall_time = 0.02
                self.submission.memory = 256
                self.submission.exit_code = 0
                self.submission.exit_signal = 0
                self.submission.message = "ok"

        monkeypatch.setattr(worker_tasks, "IsolateCodeSandbox", FakeSandbox)
        monkeypatch.setattr(
            worker_tasks, "post_data_on_callback", post_data_on_callback
        )

        result = worker_tasks.submit_submission_task(str(submission.token))

        sync_db.refresh(submission)
        assert result == f"Submission successful {submission.token}"
        assert submission.status == SandboxSubmissionStatus.acc.value
        assert submission.stdout == "hello\n"
        assert submission.stderr == ""
        assert submission.time == 0.01
        assert submission.wall_time == 0.02
        assert submission.memory == 256
        assert submission.exit_code == 0
        assert submission.exit_signal == 0
        assert submission.message == "ok"
        assert submission.finished_at is not None
        post_data_on_callback.assert_called_once()

    def test_submit_submission_task_marks_internal_worker_errors(
        self,
        mock_language_sample: Dict[str, Any],
        mock_submission_sample: Dict[str, Any],
        sync_db: Session,
        monkeypatch: pytest.MonkeyPatch,
    ):
        _create_language(mock_language_sample, sync_db)
        submission = _create_submission(mock_submission_sample, sync_db)

        class FailingSandbox:
            def __init__(self, sandbox_submission):
                self.submission = sandbox_submission

            def process_and_execute(self):
                raise RuntimeError("sandbox failure")

        monkeypatch.setattr(worker_tasks, "IsolateCodeSandbox", FailingSandbox)

        result = worker_tasks.submit_submission_task(str(submission.token))

        sync_db.refresh(submission)
        assert result == f"Submission failed {submission.token}"
        assert submission.status == SandboxSubmissionStatus.boxerr.value
        assert submission.message == "Internal worker error"
