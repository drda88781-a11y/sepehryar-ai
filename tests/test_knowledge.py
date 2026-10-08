"""
Tests for offline Knowledge Base loader, indexer, and search engine.
"""
from pathlib import Path
from app.knowledge.loader import KnowledgeLoader
from app.knowledge.indexer import KnowledgeIndexer
from app.knowledge.search import KnowledgeSearchEngine


def test_knowledge_loader_parses_markdown(tmp_path: Path):
    doc_file = tmp_path / "test_doc.md"
    doc_file.write_text("""# راهنمای کدینگ کالاها
این راهنما نحوه تعریف کالا را نشان می‌دهد.

## ساختار کد کالا
کد کالا عددی ۶ رقمی است.

## بارکد کالا
بارکد کالا در ستون BaghaliCode ثبت می‌شود.
""", encoding="utf-8")

    doc = KnowledgeLoader.load_document(doc_file, base_dir=tmp_path)
    assert doc is not None
    assert doc.title == "راهنمای کدینگ کالاها"
    assert len(doc.chunks) == 3
    assert "BaghaliCode" in doc.chunks[2].content


def test_knowledge_text_normalization():
    norm1 = KnowledgeSearchEngine.normalize_text("كتاب هاي فارسي")
    norm2 = KnowledgeSearchEngine.normalize_text("کتاب های فارسی")
    assert norm1 == norm2


def test_knowledge_search_exact_and_token_matching():
    # Test on already indexed knowledge base
    search_engine = KnowledgeSearchEngine()
    results = search_engine.search("بانک", limit=5)
    assert len(results) > 0
    # Top result should mention bank
    assert any("بانک" in r.heading or "بانک" in r.snippet for r in results)


def test_knowledge_context_generation():
    search_engine = KnowledgeSearchEngine()
    context = search_engine.get_relevant_context("مغایرت انبار", limit=2)
    assert isinstance(context, str)
