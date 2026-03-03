"""Query retrieval module.

This module provides retrieval functionality for semantic search
over indexed redacted summaries. It handles:
- Query embedding generation
- Similarity search with filtering
- Score thresholding for hallucination prevention

Usage:
    retriever = Retriever(vector_store=ChromaVectorStore(...))
    results = await retriever.retrieve("What are the high priority claims?", top_k=5)
"""

import logging
from dataclasses import dataclass
from typing import Any

from src.store.vector import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Represents a single retrieval result."""

    id: str
    text: str
    metadata: dict[str, Any]
    score: float
    email_hash: str


class RetrievalService:
    """Service for retrieving relevant documents from vector store.

    Provides:
    - Query embedding generation
    - Similarity search with metadata filtering
    - Configurable retrieval limits and thresholds

    Usage:
        retriever = RetrievalService(vector_store=ChromaVectorStore(...))
        results = await retriever.retrieve("What are the high priority claims?")
    """

    DEFAULT_TOP_K = 5
    DEFAULT_SCORE_THRESHOLD = 0.3

    def __init__(
        self,
        vector_store: VectorStore,
        top_k: int = DEFAULT_TOP_K,
        score_threshold: float = DEFAULT_SCORE_THRESHOLD,
    ):
        """Initialize the retrieval service.

        Args:
            vector_store: Vector store for document retrieval
            top_k: Default number of results to return
            score_threshold: Minimum similarity score for results
        """
        self._vector_store = vector_store
        self._top_k = top_k
        self._score_threshold = score_threshold

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict[str, Any] | None = None,
        score_threshold: float | None = None,
    ) -> list[RetrievalResult]:
        """Retrieve relevant documents for a query.

        Args:
            query: User query string
            top_k: Number of results to return (uses default if not specified)
            filters: Optional metadata filters
            score_threshold: Minimum similarity score (uses default if not specified)

        Returns:
            List of retrieval results with scores above threshold

        Raises:
            VectorStoreError: If retrieval fails
        """
        k = top_k if top_k is not None else self._top_k
        threshold = (
            score_threshold if score_threshold is not None else self._score_threshold
        )

        logger.info(
            "Retrieving documents",
            extra={"query": query[:100], "top_k": k, "threshold": threshold},
        )

        query_embedding = await self._vector_store.generate_embedding(query)

        raw_results = await self._vector_store.search(
            query_embedding=query_embedding,
            top_k=k,
            filters=filters,
        )

        results = []
        for doc in raw_results:
            score = doc.get("score", 0.0)
            if score < threshold:
                continue

            email_hash = doc.get("id", "") or doc.get("metadata", {}).get(
                "email_hash", ""
            )
            metadata = doc.get("metadata", {})

            results.append(
                RetrievalResult(
                    id=doc.get("id", ""),
                    text=doc.get("text", ""),
                    metadata=metadata,
                    score=score,
                    email_hash=email_hash,
                )
            )

        logger.info(
            "Retrieval completed",
            extra={
                "query": query[:100],
                "raw_results": len(raw_results),
                "filtered_results": len(results),
            },
        )

        return results

    async def retrieve_with_fallback(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[RetrievalResult], bool]:
        """Retrieve documents with automatic threshold fallback.

        If no results pass the threshold, retries with lower threshold.

        Args:
            query: User query string
            top_k: Number of results to return
            filters: Optional metadata filters

        Returns:
            Tuple of (results, had_to_lower_threshold)
        """
        threshold = self._score_threshold
        results = await self.retrieve(query, top_k, filters, threshold)

        if not results and threshold > 0.1:
            logger.info(
                "No results with threshold, lowering threshold",
                extra={"original_threshold": threshold},
            )
            results = await self.retrieve(query, top_k, filters, score_threshold=0.1)
            return results, True

        return results, False


class Retriever:
    """Lightweight retriever wrapper for backward compatibility.

    This class provides a simple interface for retrieval operations.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        top_k: int = 5,
        score_threshold: float = 0.3,
    ):
        """Initialize the retriever.

        Args:
            vector_store: Vector store instance
            top_k: Default number of results
            score_threshold: Minimum similarity score
        """
        self._service = RetrievalService(
            vector_store=vector_store,
            top_k=top_k,
            score_threshold=score_threshold,
        )

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """Retrieve documents for a query.

        Args:
            query: User query string
            top_k: Number of results
            filters: Optional metadata filters

        Returns:
            List of retrieval results
        """
        return await self._service.retrieve(query, top_k, filters)

    async def get_context(
        self,
        query: str,
        top_k: int = 5,
    ) -> str:
        """Get formatted context string from retrieval results.

        Args:
            query: User query string
            top_k: Number of documents to include

        Returns:
            Formatted context string with citations
        """
        results = await self.retrieve(query, top_k=top_k)

        if not results:
            return "No relevant documents found."

        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[{i}] Email Hash: {result.email_hash}\n"
                f"Classification: {result.metadata.get('classification', 'unknown')}\n"
                f"Priority: {result.metadata.get('priority', 'unknown')}\n"
                f"Content: {result.text[:500]}"
            )

        return "\n\n".join(context_parts)
