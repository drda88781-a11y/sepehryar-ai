"""
Offline Knowledge Base subsystem for Sepehryar AI Engine.
Provides local document loading, indexing, and offline semantic/keyword search.
"""
from app.knowledge.models import KnowledgeDocument, KnowledgeChunk, SearchResult
from app.knowledge.loader import KnowledgeLoader
from app.knowledge.indexer import KnowledgeIndexer, knowledge_indexer
from app.knowledge.search import KnowledgeSearchEngine, knowledge_search_engine

__all__ = [
    "KnowledgeDocument",
    "KnowledgeChunk",
    "SearchResult",
    "KnowledgeLoader",
    "KnowledgeIndexer",
    "knowledge_indexer",
    "KnowledgeSearchEngine",
    "knowledge_search_engine",
]
