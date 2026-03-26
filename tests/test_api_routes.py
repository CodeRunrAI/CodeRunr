import uuid
from typing import List, Dict, Any
from unittest.mock import ANY, MagicMock, call, patch

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from config import settings
from db.models import Language, Submission, SubmissionBatch


def test_has_all_api_routes(client: TestClient):
    routes = [route.path for route in client.app.routes]
    expected_api_routes = [
        "/api/v1/health",
        "/api/v1/languages",
        "/api/v1/languages/{language_id}",
        "/api/v1/submissions",
        "/api/v1/submissions",
        "/api/v1/submissions/batch",
        "/api/v1/submissions/batch/{token}",
        "/api/v1/submissions/{token}",
        "/api/v1/submissions/{token}",
    ]

    for valid_route in expected_api_routes:
        assert valid_route in routes


class TestHealthRoute:
    """Test health route"""

    @pytest.mark.asyncio
    async def test_route_success(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_route_success_with_n_request(self, async_client: AsyncClient):
        for _ in range(5):
            response = await async_client.get("/api/v1/health")

            assert response.status_code == 200
            assert response.json() == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_route_with_method_not_allowed(self, async_client: AsyncClient):
        methods_to_test = ["POST", "PUT", "DELETE", "PATCH"]

        for method in methods_to_test:
            response = await async_client.request(method, "/api/v1/health")
            assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_route_option_request(self, async_client: AsyncClient):
        response = await async_client.options("/api/v1/health")
        assert response.status_code in [200, 405]

    @pytest.mark.asyncio
    async def test_route_content_type(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/health")
        assert "application/json" in response.headers.get("content-type", "")


class TestLanguageRoute:
    """Test language route"""

    @pytest.mark.asyncio
    async def test_get_language(
        self, mock_language_sample: Dict[str, Any], async_client: AsyncClient
    ):
        with patch("routes.languages.get_language") as mock_service:
            mock_service.return_value = Language(**mock_language_sample)

            response = await async_client.get("/api/v1/languages/1")
            json_response = response.json()

            assert response.status_code == 200
            assert json_response["status"] == "Success"
            assert json_response["message"] == "Language response"
            assert json_response["data"] == mock_language_sample

    @pytest.mark.asyncio
    async def test_get_language_with_non_exists_id(self, async_client: AsyncClient):
        with patch("routes.languages.get_language") as mock_service:
            mock_service.return_value = None

            response = await async_client.get("/api/v1/languages/1")
            json_response = response.json()

            assert response.status_code == 404
            assert json_response["status"] == "Error"
            assert json_response["message"] == "Language not found"
            assert json_response["data"] is None

    @pytest.mark.asyncio
    async def test_get_language_with_invalid_id(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/languages/cc1")
        json_response = response.json()

        assert response.status_code == 422
        assert json_response["status"] == "Error"
        assert json_response["message"] == "Validation Error"

    @pytest.mark.asyncio
    async def test_get_all_languages(
        self, mock_language_samples: List[Dict[str, Any]], async_client: AsyncClient
    ):
        with patch("routes.languages.get_languages") as mock_service:
            mock_service.return_value = [
                Language(**data) for data in mock_language_samples
            ]

            response = await async_client.get("/api/v1/languages")
            json_response = response.json()

            assert response.status_code == 200
            assert json_response["status"] == "Success"
            assert json_response["message"] == "All languages"
            assert json_response["data"] == mock_language_samples

    @pytest.mark.asyncio
    async def test_get_all_languages_empty_list(self, async_client: AsyncClient):
        with patch("routes.languages.get_languages") as mock_service:
            mock_service.return_value = []

            response = await async_client.get("/api/v1/languages")
            json_response = response.json()

            assert response.status_code == 200
            assert json_response["status"] == "Success"
            assert json_response["message"] == "All languages"
            assert json_response["data"] == []


class TestSubmissionRoute:
    """Test submission routes"""

    @pytest.mark.asyncio
    async def test_create_submission(
        self, mock_submission_sample: Dict[str, Any], async_client: AsyncClient
    ):
        with patch("routes.submissions.create_submission") as mock_create_submission:
            mock_create_submission.return_value = Submission(**mock_submission_sample)

            with patch(
                "routes.submissions.submit_submission_task"
            ) as mock_submit_submission_task:
                mock_submit_submission_task.delay = MagicMock()

                response = await async_client.post(
                    "/api/v1/submissions", json=mock_submission_sample
                )
                json_response = response.json()

                assert response.status_code == 201
                assert json_response["message"] == "Submission Created"
                assert json_response["status"] == "Success"
                mock_create_submission.assert_awaited_once()
                assert len(mock_create_submission.await_args.args) == 2
                assert mock_create_submission.await_args.args[1].token == uuid.UUID(
                    mock_submission_sample["token"]
                )
                mock_submit_submission_task.delay.assert_called_once_with(
                    mock_submission_sample["token"]
                )

    @pytest.mark.asyncio
    async def test_create_submission_with_invalid_data(
        self, mock_submission_sample: Dict[str, Any], async_client: AsyncClient
    ):
        mock_submission_sample["token"] = "xxx"

        with patch("routes.submissions.create_submission") as mock_create_submission:
            with patch(
                "routes.submissions.submit_submission_task"
            ) as mock_submit_submission_task:
                mock_submit_submission_task.delay = MagicMock()

                response = await async_client.post(
                    "/api/v1/submissions", json=mock_submission_sample
                )
                json_response = response.json()

                assert response.status_code == 422
                assert json_response["status"] == "Error"
                assert json_response["message"] == "Validation Error"
                mock_create_submission.assert_not_awaited()
                mock_submit_submission_task.delay.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_submission_by_token_not_found(self, async_client: AsyncClient):
        token = str(uuid.uuid4())

        with patch(
            "routes.submissions.get_submission_by_token"
        ) as mock_get_submission_by_token:
            mock_get_submission_by_token.return_value = None

            response = await async_client.get(f"/api/v1/submissions/{token}")
            json_response = response.json()

            assert response.status_code == 404
            assert json_response["status"] == "Error"
            assert json_response["message"] == "Submission not found"
            assert json_response["data"] is None

    @pytest.mark.asyncio
    async def test_get_submission_in_queue(
        self, mock_submission_sample: Dict[str, Any], async_client: AsyncClient
    ):
        token = mock_submission_sample["token"]

        with patch(
            "routes.submissions.get_submission_by_token"
        ) as mock_get_submission_by_token:
            mock_get_submission_by_token.return_value = Submission(
                **mock_submission_sample
            )

            response = await async_client.get(f"/api/v1/submissions/{token}")
            json_response = response.json()

            assert response.status_code == 200
            assert json_response["status"] == "Success"
            assert json_response["message"] == "Submission data"
            assert json_response["data"] == {"token": token, "status": "Queued"}

    @pytest.mark.asyncio
    async def test_get_submission_in_processing(
        self, mock_submission_sample: Dict[str, Any], async_client: AsyncClient
    ):
        token = mock_submission_sample["token"]
        mock_submission_sample["status"] = "Processing"

        with patch(
            "routes.submissions.get_submission_by_token"
        ) as mock_get_submission_by_token:
            mock_get_submission_by_token.return_value = Submission(
                **mock_submission_sample
            )

            response = await async_client.get(f"/api/v1/submissions/{token}")
            json_response = response.json()

            assert response.status_code == 200
            assert json_response["status"] == "Success"
            assert json_response["message"] == "Submission data"
            assert json_response["data"] == {"token": token, "status": "Processing"}

    @pytest.mark.asyncio
    async def test_get_submission_in_accepted(
        self, mock_submission_sample: Dict[str, Any], async_client: AsyncClient
    ):
        token = mock_submission_sample["token"]
        mock_submission_sample["status"] = "Accepted"

        with patch(
            "routes.submissions.get_submission_by_token"
        ) as mock_get_submission_by_token:
            mock_get_submission_by_token.return_value = Submission(
                **mock_submission_sample
            )

            response = await async_client.get(f"/api/v1/submissions/{token}")
            json_response = response.json()

            from schema import SubmissionResponse

            assert response.status_code == 200
            assert json_response["status"] == "Success"
            assert json_response["message"] == "Submission data"
            assert json_response["data"]["status"] == "Accepted"
            assert SubmissionResponse.model_validate(json_response["data"])

    @pytest.mark.asyncio
    async def test_delete_submission(
        self, mock_submission_sample: Dict[str, Any], async_client: AsyncClient
    ):
        token = mock_submission_sample["token"]

        with patch("routes.submissions.delete_submission") as mock_delete_submission:
            mock_delete_submission.return_value = Submission(**mock_submission_sample)

            response = await async_client.delete(f"/api/v1/submissions/{token}")
            json_response = response.json()

            assert response.status_code == 200
            assert json_response["status"] == "Success"
            assert json_response["message"] == "Submission Deleted"
            assert json_response["data"] is None

    @pytest.mark.asyncio
    async def test_delete_submission_not_found(self, async_client: AsyncClient):
        token = str(uuid.uuid4())

        with patch("routes.submissions.delete_submission") as mock_delete_submission:
            mock_delete_submission.return_value = None

            response = await async_client.delete(f"/api/v1/submissions/{token}")
            json_response = response.json()

            assert response.status_code == 404
            assert json_response["status"] == "Error"
            assert json_response["message"] == "Submission not found"
            assert json_response["data"] is None

    @pytest.mark.asyncio
    async def test_get_all_submission(
        self, mock_submission_samples: List[Dict[str, Any]], async_client: AsyncClient
    ):
        with patch("routes.submissions.get_submissions") as mock_get_submissions:
            mock_get_submissions.return_value = [
                Submission(**data) for data in mock_submission_samples
            ]

            response = await async_client.get("/api/v1/submissions")
            json_response = response.json()

            assert response.status_code == 200
            assert json_response["status"] == "Success"
            assert json_response["message"] == "All Submissions"
            assert type(json_response["data"]) is list

            for i, data in enumerate(json_response["data"]):
                assert mock_submission_samples[i]["token"] == data["token"]
                assert mock_submission_samples[i]["status"] == data["status"]

            mock_get_submissions.assert_awaited_once()
            assert len(mock_get_submissions.await_args.args) == 1
            assert mock_get_submissions.await_args.kwargs == {"page": 1, "per_page": 20}

    @pytest.mark.asyncio
    async def test_get_all_submission_empty_list(self, async_client: AsyncClient):
        with patch("routes.submissions.get_submissions") as mock_get_submissions:
            mock_get_submissions.return_value = []

            response = await async_client.get("/api/v1/submissions")
            json_response = response.json()

            assert response.status_code == 200
            assert json_response["status"] == "Success"
            assert json_response["message"] == "All Submissions"
            assert type(json_response["data"]) is list
            assert json_response["data"] == []

    @pytest.mark.asyncio
    async def test_get_all_submission_with_pagination(
        self, mock_submission_samples: List[Dict[str, Any]], async_client: AsyncClient
    ):
        total_samples = len(mock_submission_samples)
        remaining_items = 50 - total_samples
        items = [
            {**mock_submission_samples[index % total_samples], "token": str(uuid.uuid4())}
            for index in range(remaining_items)
        ]

        mock_submission_samples.extend(items)

        page = 3
        per_page = 10

        def fake_get_submission():
            skip = max(0, (page - 1) * per_page)
            return mock_submission_samples[skip : skip + per_page]

        with patch("routes.submissions.get_submissions") as mock_get_submissions:
            mock_get_submissions.return_value = fake_get_submission()

            response = await async_client.get(
                "/api/v1/submissions", params={"page": page, "per_page": per_page}
            )
            json_response = response.json()

            assert response.status_code == 200
            assert json_response["status"] == "Success"
            assert json_response["message"] == "All Submissions"
            assert type(json_response["data"]) is list
            assert len(json_response["data"]) == 10

            for i, fake_data in enumerate(fake_get_submission()):
                assert json_response["data"][i]["token"] == fake_data["token"]

            mock_get_submissions.assert_awaited_once()
            assert len(mock_get_submissions.await_args.args) == 1
            assert mock_get_submissions.await_args.kwargs == {
                "page": page,
                "per_page": per_page,
            }

    @pytest.mark.asyncio
    async def test_create_submission_batch(
        self, mock_submission_samples: List[Dict[str, Any]], async_client: AsyncClient
    ):
        token = str(uuid.uuid4())
        submissions = [Submission(**sample) for sample in mock_submission_samples]
        submission_batch = SubmissionBatch(token=token, submissions=submissions)

        post_data = {"submissions": mock_submission_samples}

        with patch(
            "routes.submissions.create_submission_batch"
        ) as mock_create_submission_batch:
            mock_create_submission_batch.return_value = submission_batch

            with patch(
                "routes.submissions.submit_submission_task"
            ) as mock_submit_submission_task:
                mock_submit_submission_task.delay = MagicMock()

                response = await async_client.post(
                    "/api/v1/submissions/batch", json=post_data
                )
                json_response = response.json()

                assert response.status_code == 201
                assert json_response["status"] == "Success"
                assert json_response["message"] == "Submission batch created"
                assert "token" in json_response["data"]
                assert json_response["data"]["token"] == token
                mock_create_submission_batch.assert_awaited_once()
                assert len(mock_create_submission_batch.await_args.args) == 2
                mock_submit_submission_task.delay.assert_has_calls(
                    [call(sample["token"]) for sample in mock_submission_samples]
                )

        for i, submission in enumerate(json_response["data"]["submissions"]):
            assert post_data["submissions"][i]["token"] == submission["token"]
            assert post_data["submissions"][i]["status"] == submission["status"]

    @pytest.mark.asyncio
    async def test_get_submission_batch(
        self, mock_submission_samples: List[Dict[str, Any]], async_client: AsyncClient
    ):
        batch_token = str(uuid.uuid4())
        accepted_submission = {**mock_submission_samples[0], "status": "Accepted"}
        queued_submission = {**mock_submission_samples[1], "status": "Queued"}
        submission_batch = SubmissionBatch(
            token=batch_token,
            submissions=[
                Submission(**accepted_submission),
                Submission(**queued_submission),
            ],
        )

        with patch(
            "routes.submissions.get_submission_batch_by_token"
        ) as mock_get_submission_batch:
            mock_get_submission_batch.return_value = submission_batch

            response = await async_client.get(f"/api/v1/submissions/batch/{batch_token}")
            json_response = response.json()

            assert response.status_code == 200
            assert json_response["status"] == "Success"
            assert json_response["message"] == "Submission batch data"
            assert json_response["data"]["token"] == batch_token
            assert json_response["data"]["submissions"][0]["status"] == "Accepted"
            assert json_response["data"]["submissions"][1] == {
                "token": queued_submission["token"],
                "status": "Queued",
            }
            mock_get_submission_batch.assert_awaited_once()
            assert mock_get_submission_batch.await_args.args[1] == uuid.UUID(batch_token)

    @pytest.mark.asyncio
    async def test_get_submission_batch_not_found(self, async_client: AsyncClient):
        batch_token = str(uuid.uuid4())

        with patch(
            "routes.submissions.get_submission_batch_by_token"
        ) as mock_get_submission_batch:
            mock_get_submission_batch.return_value = None

            response = await async_client.get(f"/api/v1/submissions/batch/{batch_token}")
            json_response = response.json()

            assert response.status_code == 404
            assert json_response["status"] == "Error"
            assert json_response["message"] == "Batch not found"
            assert json_response["data"] is None
            mock_get_submission_batch.assert_awaited_once_with(
                ANY, uuid.UUID(batch_token)
            )


class TestAuthRoute:
    @pytest.mark.asyncio
    @pytest.mark.real_auth
    async def test_languages_requires_api_key(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/languages")
        json_response = response.json()

        assert response.status_code == 401
        assert json_response["status"] == "Error"
        assert json_response["message"] == "Unauthorized: No API key provided"

    @pytest.mark.asyncio
    @pytest.mark.real_auth
    async def test_languages_rejects_invalid_api_key(self, async_client: AsyncClient):
        response = await async_client.get(
            "/api/v1/languages", headers={"X-API-Key": "not-the-right-key"}
        )
        json_response = response.json()

        assert response.status_code == 401
        assert json_response["status"] == "Error"
        assert json_response["message"] == "Unauthorized: invalid API key"

    @pytest.mark.asyncio
    @pytest.mark.real_auth
    async def test_languages_accepts_valid_api_key(self, async_client: AsyncClient):
        with patch("routes.languages.get_languages") as mock_get_languages:
            mock_get_languages.return_value = []

            response = await async_client.get(
                "/api/v1/languages",
                headers={"X-API-Key": settings.AUTH_TOKEN.get_secret_value()},
            )
            json_response = response.json()

            assert response.status_code == 200
            assert json_response["status"] == "Success"
            assert json_response["message"] == "All languages"
            assert json_response["data"] == []
            mock_get_languages.assert_awaited_once()
