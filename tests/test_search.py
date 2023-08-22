import os
import pytest

from statschat.search import BasicSearcher


@pytest.fixture(autouse=True, scope="session")
def BM25_searcher():
    searcher = BasicSearcher(
        directory="tests/data",
        reader_model="deepset/roberta-base-squad2",
        answer_model="google/flan-t5-small",
        search_mode="BM25",
    )
    yield searcher


def test_bm25_instantiation(BM25_searcher):
    assert "BM25Retriever" in BM25_searcher.pipe.components


def test_bm25_end_to_end(BM25_searcher):
    """First sign if we break something."""
    query = "How many people lived in national parks in 2021?"
    result, _ = BM25_searcher.query(question=query)
    assert "399,400" in result["answer"]


def test_bm25_end_to_end_query_args(BM25_searcher):
    """First sign if we break something."""
    query = "How many people lived in national parks in 2021?"
    result, _ = BM25_searcher.query(question=query, k_docs=1, k_answers=1)
    assert "399,400" in result["answer"]


def test_bm25_store(BM25_searcher):
    """The document store is actually holding something."""
    doc_count = (
        BM25_searcher.indexing_pipeline.get_document_store().get_document_count()
    )
    assert doc_count == 101


def test_bm25_retrieval(BM25_searcher):
    query = "UK greenhouse gas"

    # Confirm two search results
    results = BM25_searcher.pipe.get_node("BM25Retriever").run_query(query)
    assert len(results[0]["documents"]) == 10

    # Confirm correct result
    answer = "Total UK greenhouse gas (GHG)"
    assert answer in results[0]["documents"][0].content


def remove_faiss_db(faiss_db_root):
    for a_file in ["faiss_config.json", "faiss_index.faiss", "faiss_db.db"]:
        if os.path.exists(os.path.join(faiss_db_root, a_file)):
            os.remove(os.path.join(faiss_db_root, a_file))


@pytest.fixture(autouse=True, scope="session")
def embed_searcher():
    faiss_db_root = "tests"
    remove_faiss_db(faiss_db_root)
    searcher = BasicSearcher(
        directory="tests/data",
        reader_model="deepset/roberta-base-squad2",
        answer_model="google/flan-t5-small",
        embedding_model="sentence-transformers/paraphrase-MiniLM-L3-v2",
        embedding_dim=384,
        search_mode="embedding",
        faiss_db_root=faiss_db_root,
    )
    yield searcher
    remove_faiss_db(faiss_db_root)


def test_embedding_instantiation(embed_searcher):
    """That actually worked!"""
    assert "EmbeddingRetriever" in embed_searcher.pipe.components
    assert "BM25Retriever" not in embed_searcher.pipe.components


def test_embedding_end_to_end(embed_searcher):
    """First sign if we break something."""
    query = "How many people lived in national parks in 2021?"
    result, _ = embed_searcher.query(question=query)
    assert "399,400" in result["answer"]


def test_embedding_end_to_end_query_args(embed_searcher):
    """First sign if we break something."""
    query = "How many people lived in national parks in 2021?"
    result, _ = embed_searcher.query(question=query, k_docs=6, k_answers=6)
    assert "399,400" in result["answer"]


def test_embedding_store(embed_searcher):
    """The document store is actually holding something."""
    doc_count = (
        embed_searcher.indexing_pipeline.get_document_store().get_document_count()
    )
    assert doc_count == 101


def test_embedding_retrieval(embed_searcher):
    query = "UK Greenhouse gas"

    # Confirm two search results
    results = embed_searcher.pipe.get_node("EmbeddingRetriever").run_query(query)
    assert len(results[0]["documents"]) == 10

    # Confirm correct result
    answer = "greenhouse gas emissions"
    assert answer in results[0]["documents"][0].content
