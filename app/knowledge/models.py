"""
Pydantic data models for the offline Knowledge Base.
"""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class KnowledgeChunk(BaseModel):
    """A granular section or paragraph within a knowledge document."""
    chunk_id: str
    doc_id: str
    doc_title: str
    category: str
    heading: str
    content: str
    chunk_index: int = 0
    filepath: str = ""


class KnowledgeDocument(BaseModel):
    """A full knowledge document representing a markdown or text file."""
    id: str
    title: str
    category: str
    filepath: str
    content: str
    content_hash: str
    chunks: list[KnowledgeChunk] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    indexed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SearchResult(BaseModel):
    """Result item returned by offline knowledge search."""
    doc_title: str
    category: str
    heading: str
    snippet: str
    score: float
    filepath: str
    chunk_id: Optional[str] = None
