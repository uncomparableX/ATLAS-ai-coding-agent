"""
Qdrant Vector Store
Handles storage and retrieval of code chunk embeddings and agent memory.
All operations are async-native via AsyncQdrantClient.
"""
import uuid
from typing import Any, Dict, List, Optional

import structlog
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qm

from app.core.config import settings
from app.services.indexing.repository_indexer import EmbeddingService

logger = structlog.get_logger(__name__)

# Dimension of all-MiniLM-L6-v2
VECTOR_DIM = 384


class VectorStore:
    """
    Async Qdrant client wrapper.
    Manages two collections:
      - code_chunks   : indexed source code from repositories
      - agent_memory  : episodic/semantic agent memory
    """

    def __init__(self):
        self._client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=30,
        )
        self._embedding = EmbeddingService.get_instance()

    # ── Collection Management ─────────────────────────────────────────────────

    async def ensure_collections(self):
        """Create Qdrant collections if they do not exist yet."""
        for name in (
            settings.QDRANT_CODE_COLLECTION,
            settings.QDRANT_MEMORY_COLLECTION,
        ):
            try:
                await self._client.get_collection(name)
                logger.debug("Qdrant collection already exists", name=name)
            except Exception:
                await self._client.create_collection(
                    collection_name=name,
                    vectors_config=qm.VectorParams(
                        size=VECTOR_DIM,
                        distance=qm.Distance.COSINE,
                    ),
                    optimizers_config=qm.OptimizersConfigDiff(
                        indexing_threshold=20_000,
                        memmap_threshold=50_000,
                    ),
                    hnsw_config=qm.HnswConfigDiff(
                        m=16,
                        ef_construct=100,
                        full_scan_threshold=10_000,
                    ),
                )
                logger.info("Qdrant collection created", name=name)

    # ── Code Chunks ───────────────────────────────────────────────────────────

    async def upsert_chunks(
        self,
        repository_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ):
        """
        Bulk-upsert code chunks with their pre-computed embeddings.
        Each chunk becomes a Qdrant point with the chunk dict as payload.
        """
        if not chunks:
            return

        if len(chunks) != len(embeddings):
            raise ValueError(
                f"chunks ({len(chunks)}) and embeddings ({len(embeddings)}) lengths differ"
            )

        points = [
            qm.PointStruct(
                id=str(uuid.uuid4()),
                vector=emb,
                payload={
                    "repository_id": repository_id,
                    "file_path":     chunk["file_path"],
                    "content":       chunk["content"],
                    "start_line":    chunk.get("start_line", 0),
                    "end_line":      chunk.get("end_line",   0),
                    "language":      chunk.get("language",   ""),
                    "chunk_type":    chunk.get("chunk_type", "code"),
                    "name":          chunk.get("name"),
                },
            )
            for chunk, emb in zip(chunks, embeddings)
        ]

        # Qdrant recommends batches of ≤ 1000 points
        batch_size = 500
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            await self._client.upsert(
                collection_name=settings.QDRANT_CODE_COLLECTION,
                points=batch,
                wait=True,
            )

        logger.debug(
            "Chunks upserted",
            repository_id=repository_id,
            count=len(chunks),
        )

    async def search_code(
        self,
        query: str,
        repository_id: str,
        limit: int = 10,
        language_filter: Optional[str] = None,
        chunk_type_filter: Optional[str] = None,
        score_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search over code chunks for a specific repository.
        Returns chunks sorted by cosine similarity (descending).
        """
        query_vec = self._embedding.embed_single(query)

        must: List[qm.Condition] = [
            qm.FieldCondition(
                key="repository_id",
                match=qm.MatchValue(value=repository_id),
            )
        ]

        if language_filter:
            must.append(
                qm.FieldCondition(
                    key="language",
                    match=qm.MatchValue(value=language_filter),
                )
            )

        if chunk_type_filter:
            must.append(
                qm.FieldCondition(
                    key="chunk_type",
                    match=qm.MatchValue(value=chunk_type_filter),
                )
            )

        results = await self._client.search(
            collection_name=settings.QDRANT_CODE_COLLECTION,
            query_vector=query_vec,
            query_filter=qm.Filter(must=must),
            limit=limit,
            with_payload=True,
            score_threshold=score_threshold if score_threshold > 0 else None,
        )

        return [
            {
                **r.payload,
                "relevance_score": round(r.score, 4),
                "id": str(r.id),
            }
            for r in results
        ]

    async def delete_repository(self, repository_id: str):
        """Remove all code chunk vectors for a given repository."""
        try:
            await self._client.delete(
                collection_name=settings.QDRANT_CODE_COLLECTION,
                points_selector=qm.FilterSelector(
                    filter=qm.Filter(
                        must=[
                            qm.FieldCondition(
                                key="repository_id",
                                match=qm.MatchValue(value=repository_id),
                            )
                        ]
                    )
                ),
                wait=True,
            )
            logger.info(
                "Repository vectors deleted",
                repository_id=repository_id,
            )
        except Exception as e:
            logger.warning(
                "Failed to delete repository vectors",
                repository_id=repository_id,
                error=str(e),
            )

    async def count_chunks(self, repository_id: str) -> int:
        """Return the number of indexed chunks for a repository."""
        try:
            result = await self._client.count(
                collection_name=settings.QDRANT_CODE_COLLECTION,
                count_filter=qm.Filter(
                    must=[
                        qm.FieldCondition(
                            key="repository_id",
                            match=qm.MatchValue(value=repository_id),
                        )
                    ]
                ),
                exact=True,
            )
            return result.count
        except Exception:
            return 0

    # ── Agent Memory ──────────────────────────────────────────────────────────

    async def upsert_memory(
        self,
        memory_id: str,
        content: str,
        metadata: Dict[str, Any],
    ):
        """Store an agent memory embedding in the memory collection."""
        emb = self._embedding.embed_single(content)

        await self._client.upsert(
            collection_name=settings.QDRANT_MEMORY_COLLECTION,
            points=[
                qm.PointStruct(
                    id=memory_id,
                    vector=emb,
                    payload={**metadata, "content": content},
                )
            ],
            wait=True,
        )

    async def search_memory(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 5,
        score_threshold: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search over agent memories.
        Optionally filter by repository_id, task_id, or memory_type.
        """
        query_vec = self._embedding.embed_single(query)

        must: List[qm.Condition] = []
        for key, value in (filters or {}).items():
            must.append(
                qm.FieldCondition(
                    key=key,
                    match=qm.MatchValue(value=value),
                )
            )

        results = await self._client.search(
            collection_name=settings.QDRANT_MEMORY_COLLECTION,
            query_vector=query_vec,
            query_filter=qm.Filter(must=must) if must else None,
            limit=limit,
            with_payload=True,
            score_threshold=score_threshold,
        )

        return [
            {**r.payload, "relevance_score": round(r.score, 4)}
            for r in results
        ]

    async def delete_memory(self, memory_id: str):
        """Delete a specific memory point by ID."""
        try:
            await self._client.delete(
                collection_name=settings.QDRANT_MEMORY_COLLECTION,
                points_selector=qm.PointIdsList(points=[memory_id]),
                wait=True,
            )
        except Exception as e:
            logger.warning("Failed to delete memory", id=memory_id, error=str(e))

    async def delete_repository_memory(self, repository_id: str):
        """Remove all memories associated with a repository."""
        try:
            await self._client.delete(
                collection_name=settings.QDRANT_MEMORY_COLLECTION,
                points_selector=qm.FilterSelector(
                    filter=qm.Filter(
                        must=[
                            qm.FieldCondition(
                                key="repository_id",
                                match=qm.MatchValue(value=repository_id),
                            )
                        ]
                    )
                ),
                wait=True,
            )
        except Exception as e:
            logger.warning(
                "Failed to delete repository memory",
                repository_id=repository_id,
                error=str(e),
            )
