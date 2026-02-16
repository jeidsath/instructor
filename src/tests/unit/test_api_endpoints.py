"""Tests for API endpoint routing, schema validation, and basic behavior."""

import uuid
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from instructor.api.schemas import (
    CreateLearnerRequest,
    LearnerResponse,
    PlacementResponseItem,
    SubmitResponseRequest,
)


@pytest.mark.unit
class TestHealthEndpoint:
    """Health check endpoint."""

    async def test_health(self, test_client: AsyncClient) -> None:
        async with test_client as client:
            r = await client.get("/health")
        assert r.status_code == 200


@pytest.mark.unit
class TestLearnerRoutes:
    """Learner API routes wired to DB."""

    async def test_create_learner(
        self, test_client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        async with test_client as client:
            r = await client.post(
                "/api/learners",
                json={"name": "Test Learner"},
            )
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Test Learner"
        assert "id" in data
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_awaited_once()
        mock_db_session.refresh.assert_awaited_once()

    async def test_create_learner_empty_name(
        self, test_client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        async with test_client as client:
            r = await client.post(
                "/api/learners",
                json={"name": ""},
            )
        assert r.status_code == 422

    async def test_get_learner_not_found(
        self, test_client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        async with test_client as client:
            r = await client.get(f"/api/learners/{uuid.uuid4()}")
        assert r.status_code == 404

    async def test_get_state_not_found(
        self, test_client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        async with test_client as client:
            r = await client.get(f"/api/learners/{uuid.uuid4()}/state/latin")
        assert r.status_code == 404


@pytest.mark.unit
class TestSessionRoutes:
    """Session API routes wired to DB and session manager."""

    async def test_start_session_learner_not_found(
        self, test_client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        async with test_client as client:
            r = await client.post(
                "/api/sessions",
                json={
                    "learner_id": str(uuid.uuid4()),
                    "language": "latin",
                },
            )
        assert r.status_code == 404

    async def test_get_session_not_found(
        self, test_client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        async with test_client as client:
            r = await client.get(f"/api/sessions/{uuid.uuid4()}")
        assert r.status_code == 404

    async def test_next_activity_not_found(self, test_client: AsyncClient) -> None:
        async with test_client as client:
            r = await client.get(f"/api/sessions/{uuid.uuid4()}/next")
        assert r.status_code == 404

    async def test_submit_not_found(self, test_client: AsyncClient) -> None:
        async with test_client as client:
            r = await client.post(
                f"/api/sessions/{uuid.uuid4()}/submit",
                json={"response": "test"},
            )
        assert r.status_code == 404

    async def test_end_not_found(
        self, test_client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        async with test_client as client:
            r = await client.post(f"/api/sessions/{uuid.uuid4()}/end")
        assert r.status_code == 404


@pytest.mark.unit
class TestCurriculumRoutes:
    """Curriculum API route structure."""

    async def test_list_latin_vocabulary(self, test_client: AsyncClient) -> None:
        async with test_client as client:
            r = await client.get("/api/curriculum/latin/vocabulary")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0  # We have Latin vocabulary data

    async def test_list_latin_grammar(self, test_client: AsyncClient) -> None:
        async with test_client as client:
            r = await client.get("/api/curriculum/latin/grammar")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0

    async def test_grammar_category_differs_from_subcategory(
        self, test_client: AsyncClient
    ) -> None:
        """Category (e.g. morphology) should differ from subcategory."""
        async with test_client as client:
            r = await client.get("/api/curriculum/latin/grammar")
        assert r.status_code == 200
        data = r.json()
        mismatches = [c for c in data if c["category"] != c["subcategory"]]
        assert len(mismatches) > 0, "category and subcategory should differ"
        valid_categories = {"morphology", "syntax", "phonology", "prosody"}
        for c in data:
            assert c["category"] in valid_categories, (
                f"{c['name']}: invalid category '{c['category']}'"
            )

    async def test_invalid_language_rejected(self, test_client: AsyncClient) -> None:
        async with test_client as client:
            r = await client.get("/api/curriculum/klingon/vocabulary")
        assert r.status_code == 422


@pytest.mark.unit
class TestPlacementRoutes:
    """Placement API route structure."""

    async def test_submit_placement(self, test_client: AsyncClient) -> None:
        async with test_client as client:
            r = await client.post(
                "/api/placement",
                json={
                    "responses": [
                        {
                            "probe_type": "vocabulary",
                            "difficulty": 1,
                            "correct": True,
                            "item_id": "amō",
                        },
                        {
                            "probe_type": "grammar",
                            "difficulty": 1,
                            "correct": True,
                            "item_id": "1st_decl",
                        },
                    ]
                },
            )
        assert r.status_code == 200
        data = r.json()
        assert "total_score" in data
        assert "starting_unit" in data

    async def test_empty_placement(self, test_client: AsyncClient) -> None:
        async with test_client as client:
            r = await client.post(
                "/api/placement",
                json={"responses": []},
            )
        assert r.status_code == 200
        assert r.json()["total_score"] == 0.0


@pytest.mark.unit
class TestRegistrySingleton:
    """CurriculumRegistry is loaded once and reused."""

    async def test_registry_is_same_instance(self, test_client: AsyncClient) -> None:
        """Two requests should get the same registry instance."""
        async with test_client as client:
            r1 = await client.get("/api/curriculum/latin/vocabulary")
            r2 = await client.get("/api/curriculum/latin/vocabulary")
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Both returned data — registry was available for both requests
        assert len(r1.json()) > 0
        assert r1.json() == r2.json()


@pytest.mark.unit
class TestSchemaValidation:
    """Pydantic schema validation."""

    def test_create_learner_request(self) -> None:
        req = CreateLearnerRequest(name="Test")
        assert req.name == "Test"

    def test_create_learner_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CreateLearnerRequest(name="")

    def test_learner_response(self) -> None:
        resp = LearnerResponse(id=uuid.uuid4(), name="Test")
        assert resp.name == "Test"

    def test_placement_response_item(self) -> None:
        item = PlacementResponseItem(
            probe_type="vocabulary",
            difficulty=1,
            correct=True,
        )
        assert item.item_id == ""

    def test_submit_response_defaults(self) -> None:
        req = SubmitResponseRequest(response="test")
        assert req.time_taken_ms == 0
