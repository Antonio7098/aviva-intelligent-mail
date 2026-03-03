"""Abstract vector store interface.

This module defines the VectorStore Protocol that all vector store implementations
must adhere to. This abstraction allows for:
- Easy switching between vector store providers (ChromaDB, Pinecone, etc.)
- Dependency injection of vector stores into pipeline stages
- Unit testing with mock implementations
"""

from typing import Any, Protocol, TypeVar, runtime_checkable


T = TypeVar("T", bound=dict[str, Any])


@runtime_checkable
class VectorStore(Protocol):
    """Abstract interface for vector store implementations.

    This Protocol defines the contract that all vector store implementations
    must follow. Implementations should support:
    - Document indexing with metadata
    - Similarity search with filtering
    - Document deletion by hash
    - Embedding generation via configured provider

    Example implementations:
    - ChromaVectorStore: ChromaDB-backed vector store
    - MockVectorStore: For testing

    Usage with dependency injection:
        class MyStage:
            def __init__(self, vector_store: VectorStore):
                self._vector_store = vector_store

            async def process(self, documents: list[dict]):
                await self._vector_store.index_documents(documents)
    """

    async def index_documents(
        self,
        documents: list[dict[str, Any]],
    ) -> list[str]:
        """Index documents into the vector store.

        Args:
            documents: List of documents to index. Each document should contain:
                - text: The text content to embed
                - email_hash: Pseudonymous hash of the email
                - metadata: Additional metadata (classification, priority, etc.)

        Returns:
            List of document IDs

        Raises:
            VectorStoreError: If indexing fails
        """
        ...

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar documents using a query embedding.

        Args:
            query_embedding: The embedding vector to search with
            top_k: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of matching documents with scores and metadata

        Raises:
            VectorStoreError: If search fails
        """
        ...

    async def delete_by_hash(self, email_hash: str) -> bool:
        """Delete all documents associated with an email hash.

        Args:
            email_hash: The pseudonymous hash of the email

        Returns:
            True if deletion was successful

        Raises:
            VectorStoreError: If deletion fails
        """
        ...

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate an embedding for the given text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector

        Raises:
            VectorStoreError: If embedding generation fails
        """
        ...

    async def health_check(self) -> bool:
        """Check if the vector store is healthy and accessible.

        Returns:
            True if the vector store is healthy

        Raises:
            VectorStoreError: If health check fails
        """
        ...


class VectorStoreError(Exception):
    """Base exception for vector store-related errors."""

    def __init__(
        self,
        message: str,
        is_retryable: bool = False,
    ):
        super().__init__(message)
        self.is_retryable = is_retryable


class VectorStoreConnectionError(VectorStoreError):
    """Exception raised when vector store connection fails."""

    def __init__(self, message: str):
        super().__init__(message, is_retryable=True)


class VectorStoreIndexingError(VectorStoreError):
    """Exception raised when document indexing fails."""

    def __init__(self, message: str):
        super().__init__(message, is_retryable=False)


class VectorStoreSearchError(VectorStoreError):
    """Exception raised when search fails."""

    def __init__(self, message: str):
        super().__init__(message, is_retryable=True)
