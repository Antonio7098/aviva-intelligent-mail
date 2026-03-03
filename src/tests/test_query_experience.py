"""Tests for retrieval service and hallucination guards."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.store.retrieval import RetrievalService
from src.llm.grounded_guard import GroundedGuard


class TestRetrievalService:
    """Tests for RetrievalService - semantic search over vector store."""

    @pytest.fixture
    def mock_vector_store(self):
        store = MagicMock()
        store.generate_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        store.search = AsyncMock(
            return_value=[
                {
                    "id": "hash1",
                    "text": "Test document about claims",
                    "metadata": {
                        "classification": "new_claim",
                        "priority": "p1_critical",
                    },
                    "score": 0.9,
                },
                {
                    "id": "hash2",
                    "text": "Another document about complaints",
                    "metadata": {"classification": "complaint", "priority": "p2_high"},
                    "score": 0.8,
                },
            ]
        )
        return store

    @pytest.mark.asyncio
    async def test_retrieve_returns_results_above_threshold(self, mock_vector_store):
        service = RetrievalService(mock_vector_store, top_k=5, score_threshold=0.5)
        results = await service.retrieve("What are high priority claims?")

        assert len(results) == 2
        assert results[0].email_hash == "hash1"
        assert results[0].score == 0.9

    @pytest.mark.asyncio
    async def test_retrieve_filters_below_threshold(self, mock_vector_store):
        service = RetrievalService(mock_vector_store, top_k=5, score_threshold=0.85)
        results = await service.retrieve("What are high priority claims?")

        assert len(results) == 1
        assert results[0].email_hash == "hash1"

    @pytest.mark.asyncio
    async def test_retrieve_with_fallback_lowers_threshold(self, mock_vector_store):
        mock_vector_store.search = AsyncMock(
            side_effect=[
                [{"id": "hash1", "text": "doc", "metadata": {}, "score": 0.2}],
                [{"id": "hash1", "text": "doc", "metadata": {}, "score": 0.5}],
            ]
        )
        service = RetrievalService(mock_vector_store, top_k=5, score_threshold=0.7)

        results, lowered = await service.retrieve_with_fallback("test query")

        assert lowered is True
        assert len(results) >= 1


class TestGroundedGuard:
    """Tests for GroundedGuard - hallucination prevention."""

    def test_check_retrieval_sufficient(self):
        guard = GroundedGuard(min_retrieval_count=1, min_avg_score=0.3)
        is_sufficient, msg = guard.check_retrieval(3, 0.7)

        assert is_sufficient is True
        assert "sufficient" in msg.lower()

    def test_check_retrieval_insufficient_count(self):
        guard = GroundedGuard(min_retrieval_count=2, min_avg_score=0.3)
        is_sufficient, msg = guard.check_retrieval(1, 0.7)

        assert is_sufficient is False
        assert "retrieval" in msg.lower()

    def test_check_retrieval_insufficient_score(self):
        guard = GroundedGuard(min_retrieval_count=1, min_avg_score=0.5)
        is_sufficient, msg = guard.check_retrieval(3, 0.2)

        assert is_sufficient is False
        assert "score" in msg.lower()

    def test_validate_citations_finds_citations(self):
        guard = GroundedGuard()
        answer = "According to [email_hash:hash1] and [email_hash:hash2], the claim is valid."

        is_valid, found = guard.validate_citations(answer, ["hash1", "hash2"])

        assert is_valid is True
        assert "hash1" in found
        assert "hash2" in found

    def test_validate_citations_missing_citations(self):
        guard = GroundedGuard(require_citations=True)
        answer = "The claim is valid."

        is_valid, found = guard.validate_citations(answer, ["hash1", "hash2"])

        assert is_valid is False
        assert len(found) == 0

    def test_validate_citations_no_expected(self):
        guard = GroundedGuard()
        answer = "The claim is valid."

        is_valid, found = guard.validate_citations(answer, [])

        assert is_valid is True

    def test_should_reject_weak_retrieval(self):
        guard = GroundedGuard()
        validation = {"retrieval_sufficient": False, "citations_valid": True}

        should_reject, reason = guard.should_reject(validation)

        assert should_reject is True
        assert "evidence" in reason.lower()

    def test_should_reject_missing_citations(self):
        guard = GroundedGuard(require_citations=True)
        validation = {
            "retrieval_sufficient": True,
            "citations_valid": False,
            "citations_count": 0,
        }

        should_reject, reason = guard.should_reject(validation)

        assert should_reject is True
        assert "citation" in reason.lower()

    def test_should_not_reject_valid(self):
        guard = GroundedGuard()
        validation = {
            "retrieval_sufficient": True,
            "citations_valid": True,
            "citations_count": 2,
        }

        should_reject, reason = guard.should_reject(validation)

        assert should_reject is False

    def test_get_no_evidence_message(self):
        guard = GroundedGuard()
        msg = guard.get_no_evidence_message()

        assert "evidence" in msg.lower()
        assert "documents" in msg.lower()

    def test_extract_citations_email_hash_format(self):
        guard = GroundedGuard()
        answer = "Based on [email_hash:abc123] and [email_hash:def456]"

        citations = guard._extract_citations(answer)

        assert "abc123" in citations
        assert "def456" in citations

    def test_log_guard_trigger(self):
        guard = GroundedGuard()
        guard.log_guard_trigger("test_guard", {"detail": "test"})
