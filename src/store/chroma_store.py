"""ChromaDB implementation of vector store.

This module provides a ChromaDB-backed vector store implementation
for storing and retrieving embedded redacted summaries.

It uses OpenRouter API for embedding generation with the configured
embedding model (default: nvidia/llama-nemotron-embed-vl-1b-v2:free).
"""

import logging
import os
from typing import Any

import chromadb
from openai import AsyncOpenAI

from src.app.config import settings
from src.store.vector import (
    VectorStoreConnectionError,
    VectorStoreError,
    VectorStoreIndexingError,
    VectorStoreSearchError,
)

logger = logging.getLogger(__name__)

COLLECTION_NAME = "redacted_summaries"


class OpenRouterEmbeddingClient:
    """Embedding client using OpenRouter API.

    Generates embeddings using the configured embedding model.
    """

    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = "BAAI/bge-large-en-v1.5"

    def __init__(
        self,
        base_url: str = "",
        api_key: str = "",
        model: str = "",
        timeout: int = 60,
    ):
        self._model = model or settings.embedding_model or self.DEFAULT_MODEL
        self._base_url = base_url or self.DEFAULT_BASE_URL
        self._api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")

        if not self._api_key:
            logger.warning(
                "OPENROUTER_API_KEY is not set - embedding operations will fail"
            )

        self._client = AsyncOpenAI(
            base_url=self._base_url,
            api_key=self._api_key,
            timeout=timeout,
            max_retries=0,
        )

    @property
    def model_name(self) -> str:
        return self._model

    async def embed(self, text: str) -> list[float]:
        """Generate an embedding for the given text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector

        Raises:
            VectorStoreError: If embedding generation fails
        """
        try:
            response = await self._client.embeddings.create(
                model=self._model,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise VectorStoreError(f"Failed to generate embedding: {e}") from e


class ChromaVectorStore:
    """ChromaDB-backed vector store implementation.

    Stores redacted summaries with their embeddings for semantic search.

    Usage:
        store = ChromaVectorStore(
            chroma_url="http://localhost:8001",
            collection_name="redacted_summaries"
        )
        await store.index_documents([...])
        results = await store.search(query_embedding, top_k=5)
    """

    _client = None
    _persist_directory = "/tmp/chroma_data"

    def __init__(
        self,
        chroma_url: str = "",
        collection_name: str = COLLECTION_NAME,
        embedding_client: OpenRouterEmbeddingClient | None = None,
    ):
        """Initialize the ChromaDB vector store.

        Args:
            chroma_url: URL of the ChromaDB server
            collection_name: Name of the collection to use
            embedding_client: Optional embedding client (creates default if not provided)
        """
        os.environ["CHROMA_TELEMETRY"] = "False"
        self._chroma_url = chroma_url or settings.chroma_url
        self._collection_name = collection_name
        self._embedding_client = embedding_client or OpenRouterEmbeddingClient()

        try:
            if ChromaVectorStore._client is None:
                persist_dir = os.environ.get(
                    "CHROMA_PERSIST_DIRECTORY", self._persist_directory
                )
                os.makedirs(persist_dir, exist_ok=True)
                ChromaVectorStore._client = chromadb.PersistentClient(path=persist_dir)
                logger.info(f"Using PersistentClient with directory: {persist_dir}")
        except Exception as e:
            logger.warning(
                f"Failed to use PersistentClient, falling back to EphemeralClient: {e}"
            )
            ChromaVectorStore._client = chromadb.EphemeralClient()

        self._client = ChromaVectorStore._client

    async def index_documents(
        self,
        documents: list[dict[str, Any]],
    ) -> list[str]:
        """Index documents into ChromaDB.

        Args:
            documents: List of documents to index. Each document should contain:
                - text: The text content to embed
                - email_hash: Pseudonymous hash of the email
                - metadata: Additional metadata (classification, priority, etc.)

        Returns:
            List of document IDs

        Raises:
            VectorStoreIndexingError: If indexing fails
        """
        try:
            embeddings = []
            texts = []
            metadatas = []
            ids = []

            for doc in documents:
                text = doc.get("text", "")
                email_hash = doc.get("email_hash", "")

                if not text or not email_hash:
                    logger.warning(
                        "Skipping document without text or email_hash",
                        extra={"email_hash": email_hash},
                    )
                    continue

                embedding = await self._embedding_client.embed(text)
                embeddings.append(embedding)
                texts.append(text)
                metadatas.append(doc.get("metadata", {}))
                ids.append(email_hash)

            if not ids:
                return []

            collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )

            collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids,
            )

            logger.info(
                "Indexed documents in ChromaDB",
                extra={"count": len(ids), "collection": self._collection_name},
            )

            return ids

        except VectorStoreError:
            raise
        except Exception as e:
            logger.error(f"Failed to index documents: {e}")
            raise VectorStoreIndexingError(f"Failed to index documents: {e}") from e

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
            VectorStoreSearchError: If search fails
        """
        try:
            collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters,
                include=["documents", "metadatas", "distances"],
            )

            documents = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    documents.append(
                        {
                            "id": doc_id,
                            "text": results["documents"][0][i]
                            if results["documents"]
                            else "",
                            "metadata": results["metadatas"][0][i]
                            if results["metadatas"]
                            else {},
                            "score": 1.0 - results["distances"][0][i]
                            if results["distances"]
                            else 0.0,
                        }
                    )

            logger.debug(
                "Search completed",
                extra={"query_top_k": top_k, "results_count": len(documents)},
            )

            return documents

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise VectorStoreSearchError(f"Search failed: {e}") from e

    async def delete_by_hash(self, email_hash: str) -> bool:
        """Delete all documents associated with an email hash.

        Args:
            email_hash: The pseudonymous hash of the email

        Returns:
            True if deletion was successful

        Raises:
            VectorStoreError: If deletion fails
        """
        try:
            collection = self._client.get_or_create_collection(
                name=self._collection_name,
            )
            collection.delete(ids=[email_hash])

            logger.info(
                "Deleted document from ChromaDB",
                extra={"email_hash": email_hash, "collection": self._collection_name},
            )

            return True

        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise VectorStoreError(f"Failed to delete document: {e}") from e

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate an embedding for the given text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector

        Raises:
            VectorStoreError: If embedding generation fails
        """
        return await self._embedding_client.embed(text)

    async def health_check(self) -> bool:
        """Check if ChromaDB is healthy and accessible.

        Returns:
            True if ChromaDB is healthy

        Raises:
            VectorStoreConnectionError: If health check fails
        """
        try:
            self._client.heartbeat()
            return True
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            raise VectorStoreConnectionError(
                f"ChromaDB health check failed: {e}"
            ) from e


def create_chroma_store(
    chroma_url: str = "",
    embedding_model: str = "",
) -> ChromaVectorStore:
    """Create a ChromaDB vector store.

    Args:
        chroma_url: URL of the ChromaDB server
        embedding_model: Name of the embedding model to use

    Returns:
        ChromaVectorStore instance
    """
    embedding_client = None
    if embedding_model:
        embedding_client = OpenRouterEmbeddingClient(model=embedding_model)

    return ChromaVectorStore(
        chroma_url=chroma_url,
        embedding_client=embedding_client,
    )
