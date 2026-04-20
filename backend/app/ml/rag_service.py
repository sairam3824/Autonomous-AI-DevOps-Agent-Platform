from typing import Any

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.ml.vector_store import VectorStore, vector_store

logger = get_logger(__name__)
settings = get_settings()


class RAGService:
    def __init__(self, store: VectorStore | None = None) -> None:
        self._store = store or vector_store
        self._ollama_url = settings.OLLAMA_URL
        self._model = settings.OLLAMA_MODEL

    def index_documents(
        self,
        texts: list[str],
        source: str = "upload",
        extra_metadata: dict[str, Any] | None = None,
    ) -> int:
        total_chunks = 0
        for text in texts:
            chunks = self._store.chunk_text(text, chunk_size=500, overlap=50)
            metadatas = []
            for i in range(len(chunks)):
                metadata = {"source": source, "chunk_index": i}
                if extra_metadata:
                    metadata.update(extra_metadata)
                metadatas.append(metadata)
            added = self._store.add_documents(chunks, metadatas)
            total_chunks += added

        self._store.save()
        logger.info("rag_documents_indexed", source=source, documents=len(texts), chunks=total_chunks)
        return total_chunks

    async def query(
        self,
        question: str,
        k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        search_results = self._store.search(question, k=max(k * 5, k))
        if filters:
            search_results = [
                result for result in search_results if self._matches_filters(result[1], filters)
            ]
        search_results = search_results[:k]

        if not search_results:
            return {
                "answer": "No relevant documents found. Please index some documents first.",
                "sources": [],
                "confidence": 0.0,
                "query": question,
            }

        context_parts = []
        sources = []
        for text, metadata, score in search_results:
            context_parts.append(text)
            sources.append({
                "text": text[:200] + "..." if len(text) > 200 else text,
                "source": metadata.get("source", "unknown"),
                "relevance_score": round(score, 4),
            })

        context = "\n\n---\n\n".join(context_parts)
        confidence = self._calculate_confidence(search_results)

        prompt = (
            "You are a DevOps expert assistant. Answer the question based on the provided context. "
            "If the context doesn't contain enough information, say so clearly.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )

        answer = await self._call_ollama(prompt)

        if not answer:
            answer = self._fallback_answer(question, search_results)

        return {
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "query": question,
        }

    def _matches_filters(self, metadata: dict[str, Any], filters: dict[str, Any]) -> bool:
        for key, value in filters.items():
            if metadata.get(key) != value:
                return False
        return True

    def _calculate_confidence(self, results: list[tuple[str, dict[str, Any], float]]) -> float:
        if not results:
            return 0.0
        scores = [score for _, _, score in results]
        avg_score = sum(scores) / len(scores)
        top_score = max(scores)
        confidence = (avg_score * 0.4 + top_score * 0.6)
        return round(min(max(confidence, 0.0), 1.0), 4)

    def _fallback_answer(
        self, question: str, results: list[tuple[str, dict[str, Any], float]]
    ) -> str:
        if not results:
            return "No relevant information found."

        answer_parts = [
            f"Based on indexed documents (LLM unavailable, showing raw search results):\n"
        ]
        for i, (text, metadata, score) in enumerate(results[:3], 1):
            snippet = text[:300].strip()
            answer_parts.append(f"\n**Result {i}** (relevance: {score:.2f}):\n{snippet}")

        return "\n".join(answer_parts)

    async def _call_ollama(self, prompt: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{self._ollama_url}/api/generate",
                    json={"model": self._model, "prompt": prompt, "stream": False},
                )
                resp.raise_for_status()
                return resp.json().get("response", "")
        except Exception as e:
            logger.warning("rag_ollama_call_failed", error=str(e))
            return ""

    def get_stats(self) -> dict[str, Any]:
        return self._store.get_stats()


rag_service = RAGService()
