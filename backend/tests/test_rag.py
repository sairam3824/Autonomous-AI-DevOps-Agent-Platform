import pytest

from app.ml.vector_store import VectorStore


@pytest.mark.asyncio
async def test_vector_store_add_and_search():
    store = VectorStore()
    store._store_path.mkdir(parents=True, exist_ok=True)

    texts = [
        "Kubernetes CrashLoopBackOff occurs when a container repeatedly fails to start.",
        "Docker multi-stage builds help reduce image size significantly.",
        "GitHub Actions caching can speed up CI/CD pipelines by 50 percent.",
        "Terraform state files should be stored in remote backends for team collaboration.",
    ]
    metadatas = [{"source": "test", "index": i} for i in range(len(texts))]

    added = store.add_documents(texts, metadatas)
    assert added == 4

    results = store.search("How to fix CrashLoopBackOff?", k=2)
    assert len(results) > 0
    assert len(results) <= 2

    top_text, top_meta, top_score = results[0]
    assert "CrashLoopBackOff" in top_text
    assert top_score > 0


@pytest.mark.asyncio
async def test_vector_store_stats():
    store = VectorStore()
    stats = store.get_stats()
    assert "total_documents" in stats
    assert "embedding_model" in stats


@pytest.mark.asyncio
async def test_vector_store_chunking():
    long_text = " ".join([f"word{i}" for i in range(1000)])
    chunks = VectorStore.chunk_text(long_text, chunk_size=100, overlap=10)
    assert len(chunks) > 1
    assert all(len(chunk.split()) <= 100 for chunk in chunks)


@pytest.mark.asyncio
async def test_vector_store_empty_search():
    store = VectorStore()
    results = store.search("anything", k=5)
    assert results == []
