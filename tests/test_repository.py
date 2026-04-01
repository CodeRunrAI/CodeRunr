import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, StatementError

from db.repository.languages import create_language, get_language, get_languages
from db.repository.sync_queries import get_language_sync, get_submission_by_token_sync
from db.repository.submissions import (
    create_submission,
    get_submission_by_token,
    get_submissions,
    delete_submission,
    create_submission_batch,
    get_submission_batch_by_token,
    update_submission,
)
from db.models import Language
from schema import LanguageCreate, SubmissionCreate


class TestLanguageRepository:
    @pytest.mark.asyncio
    async def test_create_language(
        self, mock_language_sample: Dict[str, Any], db: AsyncSession
    ):
        language_data = LanguageCreate.model_validate(mock_language_sample)
        language_created = await create_language(db, language_data)

        assert hasattr(language_created, "id") and language_created.id == 1
        assert language_created.name == language_data.name
        assert language_created.version == language_data.version
        assert language_created.run_cmd == language_data.run_cmd
        assert language_created.compile_cmd == language_data.compile_cmd
        assert language_created.is_archived == language_data.is_archived

    @pytest.mark.asyncio
    async def test_create_language_with_no_name(
        self, mock_language_sample: Dict[str, Any], db: AsyncSession
    ):
        mock_language_sample["name"] = None
        language_data = LanguageCreate.model_construct(**mock_language_sample)

        with pytest.raises(IntegrityError):
            await create_language(db, language_data)

    @pytest.mark.asyncio
    async def test_create_language_with_no_version(
        self, mock_language_sample: Dict[str, Any], db: AsyncSession
    ):
        mock_language_sample["version"] = None
        language_data = LanguageCreate.model_construct(**mock_language_sample)

        with pytest.raises(IntegrityError):
            await create_language(db, language_data)

    @pytest.mark.asyncio
    async def test_create_language_with_no_run_cmd(
        self, mock_language_sample: Dict[str, Any], db: AsyncSession
    ):
        mock_language_sample["run_cmd"] = None
        language_data = LanguageCreate.model_construct(**mock_language_sample)

        with pytest.raises(IntegrityError):
            await create_language(db, language_data)

    @pytest.mark.asyncio
    async def test_create_language_with_no_source_file(
        self, mock_language_sample: Dict[str, Any], db: AsyncSession
    ):
        mock_language_sample["source_file"] = None
        language_data = LanguageCreate.model_construct(**mock_language_sample)

        with pytest.raises(IntegrityError):
            await create_language(db, language_data)

    @pytest.mark.asyncio
    async def test_create_language_with_invalid_archive_value(
        self, mock_language_sample: Dict[str, Any], db: AsyncSession
    ):
        mock_language_sample["is_archived"] = "False"
        language_data = LanguageCreate.model_construct(**mock_language_sample)

        with pytest.raises(StatementError):
            await create_language(db, language_data)

    @pytest.mark.asyncio
    async def test_get_language(
        self, mock_language_sample: Dict[str, Any], db: AsyncSession, sync_db
    ):
        language_data = LanguageCreate.model_validate(mock_language_sample)
        language_created = await create_language(db, language_data)
        language_get = await get_language(db, language_created.id)

        assert language_created.id == language_get.id
        assert language_created.name == language_get.name
        assert language_created.version == language_get.version
        assert language_created.run_cmd == language_get.run_cmd
        assert language_created.compile_cmd == language_get.compile_cmd
        assert language_created.is_archived == language_get.is_archived

        # Also test the sync query
        language_get = get_language_sync(sync_db, language_created.id)

        assert language_created.id == language_get.id
        assert language_created.name == language_get.name
        assert language_created.version == language_get.version
        assert language_created.run_cmd == language_get.run_cmd
        assert language_created.compile_cmd == language_get.compile_cmd
        assert language_created.is_archived == language_get.is_archived

    @pytest.mark.asyncio
    async def test_get_language_not_found(self, db: AsyncSession, sync_db):
        language_get = await get_language(db, 1)
        assert language_get is None

        language_get = get_language_sync(sync_db, 1)
        assert language_get is None

    @pytest.mark.asyncio
    async def test_get_languages(
        self, mock_language_samples: List[Dict[str, Any]], db: AsyncSession
    ):
        language_data_list = [
            LanguageCreate.model_validate(sample) for sample in mock_language_samples
        ]
        language_created_list: List[Language] = []

        for language_data in language_data_list:
            language_created = await create_language(db, language_data)
            language_created_list.append(language_created)

        all_languages_list = await get_languages(db)

        for obj1, obj2 in zip(language_created_list, all_languages_list):
            assert obj1.id == obj2.id
            assert obj1.name == obj2.name
            assert obj1.version == obj2.version
            assert obj1.run_cmd == obj2.run_cmd
            assert obj1.compile_cmd == obj2.compile_cmd
            assert obj1.is_archived == obj2.is_archived

    @pytest.mark.asyncio
    async def test_get_languages_not_found(self, db: AsyncSession):
        language_get = await get_languages(db)
        assert language_get == []


class TestSubmissionRepository:
    @pytest_asyncio.fixture(autouse=True)
    async def sample_language(
        self, mock_language_samples: List[Dict[str, Any]], db: AsyncSession
    ):
        languages = [
            Language(**mock_language_sample)
            for mock_language_sample in mock_language_samples
        ]
        db.add_all(languages)
        await db.commit()
        return languages

    @pytest.mark.asyncio
    async def test_create_submission(
        self,
        mock_submission_sample: Dict[str, Any],
        db: AsyncSession,
    ):
        submission_data = SubmissionCreate.model_validate(mock_submission_sample)
        submission_created = await create_submission(db, submission_data)

        assert hasattr(submission_created, "id") and submission_created.id == 1
        assert submission_created.token == uuid.UUID(mock_submission_sample["token"])
        assert submission_created.source_code == mock_submission_sample["source_code"]
        assert submission_created.language_id == mock_submission_sample["language_id"]
        assert submission_created.status == mock_submission_sample["status"]

    @pytest.mark.asyncio
    async def test_create_submission_with_auto_generated_token(
        self, mock_submission_sample: Dict[str, Any], db: AsyncSession
    ):
        mock_submission_sample["token"] = None
        submission_data = SubmissionCreate.model_validate(mock_submission_sample)
        submission_created = await create_submission(db, submission_data)

        assert submission_created.id == 1
        assert isinstance(submission_created.token, uuid.UUID)
        assert submission_created.source_code == mock_submission_sample["source_code"]

    @pytest.mark.asyncio
    async def test_create_submission_with_duplicate_token(
        self, mock_submission_sample: Dict[str, Any], db: AsyncSession
    ):
        first_submission = SubmissionCreate.model_validate(mock_submission_sample)
        await create_submission(db, first_submission)

        duplicate_sample = {**mock_submission_sample, "source_code": "print('Again')"}
        duplicate_submission = SubmissionCreate.model_validate(duplicate_sample)

        with pytest.raises(IntegrityError):
            await create_submission(db, duplicate_submission)

    @pytest.mark.asyncio
    async def test_create_submission_with_invalid_language_id(
        self,
        mock_submission_sample: Dict[str, Any],
        db: AsyncSession,
    ):
        mock_submission_sample["language_id"] = 10  # Invalid
        submission = SubmissionCreate.model_validate(mock_submission_sample)

        with pytest.raises(IntegrityError):
            await create_submission(db, submission)

    @pytest.mark.asyncio
    async def test_update_submission(
        self,
        mock_submission_sample: Dict[str, Any],
        db: AsyncSession,
    ):
        submission = SubmissionCreate.model_validate(mock_submission_sample)
        new_submission = await create_submission(db, submission)

        assert new_submission.language_id != 1
        assert new_submission.source_code != "cout << 'Hello World'"

        data_to_update = {
            "language_id": 1,  # c++
            "source_code": "cout << 'Hello World'",
        }
        updated_submission = await update_submission(
            db, new_submission.token, data_to_update
        )

        assert updated_submission.language_id == 1
        assert updated_submission.source_code == "cout << 'Hello World'"

    @pytest.mark.asyncio
    async def test_update_submission_with_no_existing_submission(
        self,
        mock_submission_sample: Dict[str, Any],
        db: AsyncSession,
    ):
        data_to_update = {
            "language_id": 1,  # c++
            "source_code": "cout << 'Hello World'",
        }
        updated_submission = await update_submission(
            db, uuid.UUID(mock_submission_sample["token"]), data_to_update
        )

        assert updated_submission is None

    @pytest.mark.asyncio
    async def test_get_submission_by_token(
        self, mock_submission_sample: Dict[str, Any], db: AsyncSession, sync_db
    ):
        submission_data = SubmissionCreate.model_validate(mock_submission_sample)
        submission_created = await create_submission(db, submission_data)
        submission_get = await get_submission_by_token(db, submission_created.token)

        assert submission_get is not None
        assert submission_get.id == submission_created.id
        assert submission_get.token == submission_created.token
        assert submission_get.status == submission_created.status
        assert submission_get.source_code == submission_created.source_code
        assert submission_get.language_id == submission_created.language_id

        # Test with sync query
        submission_get = get_submission_by_token_sync(sync_db, submission_created.token)

        assert submission_get is not None
        assert submission_get.id == submission_created.id
        assert submission_get.token == submission_created.token
        assert submission_get.status == submission_created.status
        assert submission_get.source_code == submission_created.source_code
        assert submission_get.language_id == submission_created.language_id

    @pytest.mark.asyncio
    async def test_get_submission_by_token_not_found(self, db: AsyncSession, sync_db):
        submission_get = await get_submission_by_token(db, uuid.uuid4())
        assert submission_get is None

        submission_get = get_submission_by_token_sync(sync_db, uuid.uuid4())
        assert submission_get is None

    @pytest.mark.asyncio
    async def test_get_submissions(
        self, mock_submission_samples: List[Dict[str, Any]], db: AsyncSession
    ):
        base_time = datetime(2026, 1, 1, 0, 0, 0)
        created_submissions = []

        for index, sample in enumerate(mock_submission_samples):
            submission_data = SubmissionCreate.model_validate(sample)
            submission_created = await create_submission(db, submission_data)
            submission_created.created_at = base_time + timedelta(seconds=index)
            created_submissions.append(submission_created)

        await db.commit()

        submissions = await get_submissions(db)

        assert len(submissions) == len(mock_submission_samples)
        expected_tokens = [
            created_submissions[3].token,
            created_submissions[2].token,
            created_submissions[1].token,
            created_submissions[0].token,
        ]
        assert [submission.token for submission in submissions] == expected_tokens

    @pytest.mark.asyncio
    async def test_get_submissions_with_pagination(
        self, mock_submission_samples: List[Dict[str, Any]], db: AsyncSession
    ):
        base_time = datetime(2026, 1, 1, 0, 0, 0)
        created_submissions = []
        expanded_samples = [
            {
                **mock_submission_samples[index % len(mock_submission_samples)],
                "token": str(uuid.uuid4()),
            }
            for index in range(6)
        ]

        for index, sample in enumerate(expanded_samples):
            submission_data = SubmissionCreate.model_validate(sample)
            submission_created = await create_submission(db, submission_data)
            submission_created.created_at = base_time + timedelta(seconds=index)
            created_submissions.append(submission_created)

        await db.commit()

        submissions = await get_submissions(db, page=2, per_page=2)

        assert len(submissions) == 2
        expected_tokens = [created_submissions[3].token, created_submissions[2].token]
        assert [submission.token for submission in submissions] == expected_tokens

    @pytest.mark.asyncio
    async def test_delete_submission(
        self, mock_submission_sample: Dict[str, Any], db: AsyncSession
    ):
        submission_data = SubmissionCreate.model_validate(mock_submission_sample)
        submission_created = await create_submission(db, submission_data)

        deleted = await delete_submission(db, submission_created.token)
        submission_get = await get_submission_by_token(db, submission_created.token)

        assert deleted is True
        assert submission_get is None

    @pytest.mark.asyncio
    async def test_delete_submission_not_found(self, db: AsyncSession):
        deleted = await delete_submission(db, uuid.uuid4())

        assert deleted is False

    @pytest.mark.asyncio
    async def test_create_submission_batch(
        self, mock_submission_samples: List[Dict[str, Any]], db: AsyncSession
    ):
        submissions_data = [
            SubmissionCreate.model_validate(sample)
            for sample in mock_submission_samples[:2]
        ]

        batch_created = await create_submission_batch(db, submissions_data)

        assert hasattr(batch_created, "id") and batch_created.id == 1
        assert isinstance(batch_created.token, uuid.UUID)
        assert len(batch_created.submissions) == 2
        assert all(
            submission.batch_id == batch_created.id
            for submission in batch_created.submissions
        )
        assert [submission.token for submission in batch_created.submissions] == [
            uuid.UUID(sample["token"]) for sample in mock_submission_samples[:2]
        ]

    @pytest.mark.asyncio
    async def test_get_submission_batch_by_token(
        self, mock_submission_samples: List[Dict[str, Any]], db: AsyncSession
    ):
        submissions_data = [
            SubmissionCreate.model_validate(sample)
            for sample in mock_submission_samples[:2]
        ]
        batch_created = await create_submission_batch(db, submissions_data)

        batch_get = await get_submission_batch_by_token(db, batch_created.token)

        assert batch_get is not None
        assert batch_get.id == batch_created.id
        assert batch_get.token == batch_created.token
        assert len(batch_get.submissions) == len(batch_created.submissions)
        assert {submission.token for submission in batch_get.submissions} == {
            submission.token for submission in batch_created.submissions
        }

    @pytest.mark.asyncio
    async def test_get_submission_batch_by_token_not_found(self, db: AsyncSession):
        batch_get = await get_submission_batch_by_token(db, uuid.uuid4())
        assert batch_get is None
