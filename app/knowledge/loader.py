"""
Document loader and chunking engine for offline markdown and text files.
"""
import hashlib
import re
from pathlib import Path
from typing import Optional
from app.core.logger import get_logger
from app.knowledge.models import KnowledgeDocument, KnowledgeChunk

logger = get_logger("knowledge.loader")


class KnowledgeLoader:
    """Loads and chunks knowledge base markdown and text documents from local filesystem."""

    @classmethod
    def compute_hash(cls, content: str) -> str:
        """Calculate SHA-256 hash of document string."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @classmethod
    def load_document(cls, file_path: Path, base_dir: Optional[Path] = None) -> Optional[KnowledgeDocument]:
        """Load a single markdown/text file, parse title and chunks."""
        try:
            if not file_path.exists() or not file_path.is_file():
                return None

            content = file_path.read_text(encoding="utf-8", errors="replace").strip()
            if not content:
                return None

            content_hash = cls.compute_hash(content)
            doc_id = hashlib.md5(str(file_path.resolve()).encode("utf-8")).hexdigest()

            # Determine category from relative parent folder
            category = "general"
            if base_dir and base_dir in file_path.parents:
                rel_parent = file_path.relative_to(base_dir).parent
                if str(rel_parent) != ".":
                    category = str(rel_parent).replace("\\", "/")
            elif file_path.parent.name:
                category = file_path.parent.name

            # Extract Document Title (first # heading or file stem)
            title = file_path.stem.replace("_", " ").title()
            for line in content.splitlines():
                line_str = line.strip()
                if line_str.startswith("# "):
                    title = line_str.lstrip("# ").strip()
                    break

            # Parse Chunks by Headings (##, ###)
            chunks = cls._parse_chunks(doc_id, title, category, content, str(file_path))

            # Extract tags (from categories and headings)
            tags = {category.lower()}
            for ch in chunks:
                if ch.heading:
                    for word in re.findall(r"[\w\u0600-\u06FF]+", ch.heading.lower()):
                        if len(word) > 2:
                            tags.add(word)

            return KnowledgeDocument(
                id=doc_id,
                title=title,
                category=category,
                filepath=str(file_path.resolve()),
                content=content,
                content_hash=content_hash,
                chunks=chunks,
                tags=sorted(list(tags))
            )

        except Exception as e:
            logger.error(f"Failed to load knowledge document {file_path}: {e}")
            return None

    @classmethod
    def _parse_chunks(
        cls,
        doc_id: str,
        doc_title: str,
        category: str,
        content: str,
        filepath: str
    ) -> list[KnowledgeChunk]:
        """Split document into coherent chunks by markdown headers."""
        chunks: list[KnowledgeChunk] = []
        lines = content.splitlines()

        current_heading = doc_title
        current_lines: list[str] = []
        chunk_idx = 0

        header_regex = re.compile(r"^(#{1,4})\s+(.+)$")

        for line in lines:
            m = header_regex.match(line.strip())
            if m:
                # Flush previous section if substantial
                text = "\n".join(current_lines).strip()
                if text:
                    ch_id = f"{doc_id}_{chunk_idx}"
                    chunks.append(KnowledgeChunk(
                        chunk_id=ch_id,
                        doc_id=doc_id,
                        doc_title=doc_title,
                        category=category,
                        heading=current_heading,
                        content=text,
                        chunk_index=chunk_idx,
                        filepath=filepath
                    ))
                    chunk_idx += 1
                    current_lines = []

                current_heading = m.group(2).strip()
            else:
                current_lines.append(line)

        # Flush final section
        final_text = "\n".join(current_lines).strip()
        if final_text:
            ch_id = f"{doc_id}_{chunk_idx}"
            chunks.append(KnowledgeChunk(
                chunk_id=ch_id,
                doc_id=doc_id,
                doc_title=doc_title,
                category=category,
                heading=current_heading,
                content=final_text,
                chunk_index=chunk_idx,
                filepath=filepath
            ))

        # If document had no headers or single tiny text, provide full chunk
        if not chunks and content:
            chunks.append(KnowledgeChunk(
                chunk_id=f"{doc_id}_0",
                doc_id=doc_id,
                doc_title=doc_title,
                category=category,
                heading=doc_title,
                content=content,
                chunk_index=0,
                filepath=filepath
            ))

        return chunks

    @classmethod
    def load_directory(cls, directory_path: Path) -> list[KnowledgeDocument]:
        """Recursively scan and load all markdown and text documents in a directory."""
        if not directory_path.exists():
            logger.warning(f"Knowledge directory does not exist: {directory_path}")
            return []

        docs: list[KnowledgeDocument] = []
        for ext in ["*.md", "*.txt"]:
            for f in directory_path.rglob(ext):
                if f.is_file():
                    doc = cls.load_document(f, base_dir=directory_path)
                    if doc:
                        docs.append(doc)

        logger.info(f"Loaded {len(docs)} documents from {directory_path}")
        return docs
