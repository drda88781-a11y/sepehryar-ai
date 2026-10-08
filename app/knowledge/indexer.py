"""
Knowledge Base indexing coordinator for synchronizing documents with SQLite.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any
from app.config.settings import settings
from app.core.logger import get_logger
from app.knowledge.loader import KnowledgeLoader
from app.knowledge.models import KnowledgeDocument, KnowledgeChunk
from app.storage.sqlite import sqlite_manager

logger = get_logger("knowledge.indexer")


class KnowledgeIndexer:
    """Manages indexing and persistence of knowledge base documents and chunks in SQLite."""

    def __init__(self, manager=sqlite_manager) -> None:
        self.manager = manager

    def index_directory(self, directory_path: Optional[Path] = None, force_refresh: bool = False) -> dict[str, int]:
        """
        Scan directory, compare hashes against SQLite, and update documents/chunks.
        Returns dict with statistics on indexed, skipped, and total chunks.
        """
        target_dir = directory_path or settings.knowledge_path
        if not target_dir.exists():
            logger.warning(f"Knowledge path does not exist: {target_dir}")
            return {"indexed": 0, "skipped": 0, "total_chunks": 0}

        docs = KnowledgeLoader.load_directory(target_dir)
        stats = {"indexed": 0, "skipped": 0, "total_chunks": 0}

        with self.manager.get_connection() as conn:
            # Query existing document hashes
            existing_rows = conn.execute("SELECT id, content_hash FROM knowledge_documents;").fetchall()
            existing_hashes = {r["id"]: r["content_hash"] for r in existing_rows}

            for doc in docs:
                curr_hash = existing_hashes.get(doc.id)
                if not force_refresh and curr_hash == doc.content_hash:
                    # Content unchanged, skip re-indexing
                    stats["skipped"] += 1
                    stats["total_chunks"] += len(doc.chunks)
                    continue

                # Delete existing chunks for this doc if updating
                conn.execute("DELETE FROM knowledge_chunks WHERE doc_id = ?;", (doc.id,))

                # Insert or update doc
                meta_json = json.dumps({"tags": doc.tags, "chunk_count": len(doc.chunks)}, ensure_ascii=False)
                now = datetime.now(timezone.utc).isoformat()

                conn.execute(
                    """
                    INSERT INTO knowledge_documents (id, title, category, filepath, content_hash, doc_metadata_json, indexed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        title=excluded.title,
                        category=excluded.category,
                        filepath=excluded.filepath,
                        content_hash=excluded.content_hash,
                        doc_metadata_json=excluded.doc_metadata_json,
                        indexed_at=excluded.indexed_at;
                    """,
                    (doc.id, doc.title, doc.category, doc.filepath, doc.content_hash, meta_json, now)
                )

                # Insert chunks
                for chunk in doc.chunks:
                    conn.execute(
                        """
                        INSERT INTO knowledge_chunks (chunk_id, doc_id, doc_title, category, heading, content, chunk_index, filepath)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(chunk_id) DO UPDATE SET
                            heading=excluded.heading,
                            content=excluded.content,
                            category=excluded.category,
                            filepath=excluded.filepath;
                        """,
                        (chunk.chunk_id, chunk.doc_id, chunk.doc_title, chunk.category, chunk.heading, chunk.content, chunk.chunk_index, chunk.filepath)
                    )

                stats["indexed"] += 1
                stats["total_chunks"] += len(doc.chunks)

        logger.info(f"Knowledge indexing completed: {stats['indexed']} indexed, {stats['skipped']} skipped, {stats['total_chunks']} chunks total.")
        return stats

    def get_stats(self) -> dict[str, int]:
        """Return total count of indexed documents and chunks."""
        with self.manager.get_connection() as conn:
            docs_count = conn.execute("SELECT COUNT(*) as c FROM knowledge_documents;").fetchone()["c"]
            chunks_count = conn.execute("SELECT COUNT(*) as c FROM knowledge_chunks;").fetchone()["c"]
            return {"documents": docs_count, "chunks": chunks_count}

    def list_documents(self) -> list[dict[str, Any]]:
        """Return summary of all indexed knowledge documents."""
        with self.manager.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, title, category, filepath, indexed_at, doc_metadata_json
                FROM knowledge_documents
                ORDER BY category ASC, title ASC;
                """
            ).fetchall()
            return [dict(r) for r in rows]


# Singleton instance
knowledge_indexer = KnowledgeIndexer()
