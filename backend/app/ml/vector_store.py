import hashlib
import os
import pickle
from pathlib import Path
from typing import Any

import numpy as np

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

EMBEDDING_DIM = 384


class VectorStore:
    def __init__(self) -> None:
        self._index = None
        self._embeddings: np.ndarray | None = None
        self._documents: list[str] = []
        self._metadatas: list[dict[str, Any]] = []
        self._embedder = None
        self._embedding_dim = EMBEDDING_DIM
        self._store_path = Path(settings.VECTOR_STORE_PATH)
        self._store_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _get_faiss():
        try:
            import faiss
        except ModuleNotFoundError:
            return None
        return faiss

    def _load_embedder(self):
        if self._embedder is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
            self._embedding_dim = self._embedder.get_sentence_embedding_dimension()
            logger.info("embedder_loaded", model=settings.EMBEDDING_MODEL, dim=self._embedding_dim)
        except Exception as e:
            logger.warning("embedder_load_failed", error=str(e), fallback="hash-based")
            self._embedder = None

    def _hash_embedding(self, text: str) -> np.ndarray:
        h = hashlib.sha256(text.encode()).digest()
        arr = np.frombuffer(h * (self._embedding_dim // len(h) + 1), dtype=np.uint8)[: self._embedding_dim]
        vec = arr.astype(np.float32) / 255.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def _embed(self, texts: list[str]) -> np.ndarray:
        self._load_embedder()
        if self._embedder is not None:
            embeddings = self._embedder.encode(texts, show_progress_bar=False, convert_to_numpy=True)
            return embeddings.astype(np.float32)
        return np.array([self._hash_embedding(t) for t in texts], dtype=np.float32)

    def _ensure_index(self) -> None:
        if self._index is None:
            faiss = self._get_faiss()
            if faiss is None:
                logger.warning("faiss_unavailable", fallback="numpy-search")
                return
            self._index = faiss.IndexFlatIP(self._embedding_dim)
            logger.info("faiss_index_created", dim=self._embedding_dim)

    def _store_fallback_embeddings(self, embeddings: np.ndarray) -> None:
        if self._embeddings is None:
            self._embeddings = embeddings.copy()
        else:
            self._embeddings = np.vstack([self._embeddings, embeddings])

    def _rebuild_numpy_embeddings(self) -> None:
        if not self._documents:
            self._embeddings = None
            return
        self._embeddings = self._embed(self._documents)

    def _ensure_runtime_index(self) -> None:
        if self._index is not None:
            return

        faiss = self._get_faiss()
        if faiss is None:
            if self._embeddings is None and self._documents:
                self._rebuild_numpy_embeddings()
            return

        if not self._documents:
            self._ensure_index()
            return

        if self._embeddings is None:
            self._rebuild_numpy_embeddings()
        if self._embeddings is None:
            return

        self._ensure_index()
        if self._index is not None and self._index.ntotal == 0:
            embeddings = self._embeddings.copy()
            faiss.normalize_L2(embeddings)
            self._index.add(embeddings)

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        words = text.split()
        if len(words) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            start = end - overlap
        return chunks

    def add_documents(self, texts: list[str], metadatas: list[dict[str, Any]] | None = None) -> int:
        if not texts:
            return 0

        self._ensure_index()
        embeddings = self._embed(texts)
        self._store_fallback_embeddings(embeddings)

        faiss = self._get_faiss()
        if faiss is not None and self._index is not None:
            normalized = embeddings.copy()
            faiss.normalize_L2(normalized)
            self._index.add(normalized)

        for i, text in enumerate(texts):
            self._documents.append(text)
            meta = metadatas[i] if metadatas and i < len(metadatas) else {}
            self._metadatas.append(meta)

        logger.info("documents_added", count=len(texts), total=len(self._documents))
        return len(texts)

    def search(self, query: str, k: int = 5) -> list[tuple[str, dict[str, Any], float]]:
        self._ensure_runtime_index()

        if self._index is not None and self._index.ntotal > 0:
            faiss = self._get_faiss()
            if faiss is None:
                logger.warning("faiss_index_present_but_module_missing", fallback="numpy-search")
            else:
                query_embedding = self._embed([query])
                faiss.normalize_L2(query_embedding)

                actual_k = min(k, self._index.ntotal)
                scores, indices = self._index.search(query_embedding, actual_k)

                results = []
                for score, idx in zip(scores[0], indices[0]):
                    if idx < 0 or idx >= len(self._documents):
                        continue
                    results.append((
                        self._documents[idx],
                        self._metadatas[idx],
                        float(score),
                    ))
                return results

        if self._embeddings is None or len(self._documents) == 0:
            return []

        query_embedding = self._embed([query])
        doc_norms = np.linalg.norm(self._embeddings, axis=1, keepdims=True)
        safe_doc_norms = np.where(doc_norms == 0, 1.0, doc_norms)
        normalized_docs = self._embeddings / safe_doc_norms

        query_norm = np.linalg.norm(query_embedding, axis=1, keepdims=True)
        safe_query_norm = np.where(query_norm == 0, 1.0, query_norm)
        normalized_query = query_embedding / safe_query_norm

        scores = normalized_docs @ normalized_query[0]
        actual_k = min(k, len(scores))
        if actual_k == 0:
            return []
        top_indices = np.argsort(scores)[::-1][:actual_k]

        results = []
        for idx in top_indices:
            results.append((
                self._documents[int(idx)],
                self._metadatas[int(idx)],
                float(scores[int(idx)]),
            ))
        return results

    def save(self) -> None:
        faiss = self._get_faiss()
        if self._index is not None and faiss is not None:
            index_path = self._store_path / "index.faiss"
            faiss.write_index(self._index, str(index_path))

        data_path = self._store_path / "documents.pkl"
        with open(data_path, "wb") as f:
            pickle.dump(
                {
                    "documents": self._documents,
                    "metadatas": self._metadatas,
                    "embeddings": self._embeddings,
                },
                f,
            )

        logger.info("vector_store_saved", path=str(self._store_path), docs=len(self._documents))

    def load(self) -> bool:
        index_path = self._store_path / "index.faiss"
        data_path = self._store_path / "documents.pkl"

        if not index_path.exists() or not data_path.exists():
            if not data_path.exists():
                return False

        try:
            with open(data_path, "rb") as f:
                data = pickle.load(f)
            self._documents = data["documents"]
            self._metadatas = data["metadatas"]
            self._embeddings = data.get("embeddings")

            faiss = self._get_faiss()
            if index_path.exists() and faiss is not None:
                self._index = faiss.read_index(str(index_path))
            else:
                self._index = None
                self._ensure_runtime_index()

            logger.info("vector_store_loaded", docs=len(self._documents))
            return True
        except Exception as e:
            logger.error("vector_store_load_failed", error=str(e))
            return False

    def get_stats(self) -> dict[str, Any]:
        total_docs = len(self._documents)
        index_size = 0
        index_path = self._store_path / "index.faiss"
        if index_path.exists():
            index_size = os.path.getsize(index_path)

        total_chunks = 0
        if self._index is not None:
            total_chunks = self._index.ntotal
        elif self._embeddings is not None:
            total_chunks = int(self._embeddings.shape[0])

        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "index_size_bytes": index_size,
            "embedding_model": settings.EMBEDDING_MODEL,
            "embedding_dim": self._embedding_dim,
        }

    def clear(self) -> None:
        self._index = None
        self._embeddings = None
        self._documents = []
        self._metadatas = []
        logger.info("vector_store_cleared")


vector_store = VectorStore()
