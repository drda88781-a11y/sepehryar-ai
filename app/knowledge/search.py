"""
Offline Knowledge Base search engine with Persian and English text scoring.
"""
import re
from typing import Optional
from app.core.logger import get_logger
from app.knowledge.models import SearchResult
from app.storage.sqlite import sqlite_manager

logger = get_logger("knowledge.search")


class KnowledgeSearchEngine:
    """Zero-dependency local search engine for knowledge base documents."""

    def __init__(self, manager=sqlite_manager) -> None:
        self.manager = manager

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Normalize Persian, Arabic, and English characters for accurate matching."""
        if not text:
            return ""
        s = text.lower()
        # Arabic character replacements
        s = s.replace("ي", "ی").replace("ك", "ک").replace("ة", "ه").replace("ۀ", "ه")
        # Remove Persian zero-width non-joiner for unified matching
        s = s.replace("\u200c", " ")
        # Clean redundant spaces
        s = re.sub(r"\s+", " ", s)
        return s.strip()

    @classmethod
    def tokenize(cls, text: str) -> list[str]:
        """Extract meaningful alphanumeric and Persian/Arabic word tokens."""
        norm = cls.normalize_text(text)
        tokens = re.findall(r"[\w\u0600-\u06FF]+", norm)
        # Filter out common 1-character tokens except digits
        return [t for t in tokens if len(t) > 1 or t.isdigit()]

    def search(
        self,
        query: str,
        limit: int = 5,
        category: Optional[str] = None
    ) -> list[SearchResult]:
        """
        Search knowledge base chunks using token scoring and phrase proximity.
        """
        clean_q = self.normalize_text(query)
        q_tokens = self.tokenize(query)
        if not q_tokens:
            return []

        # Retrieve candidates from SQLite
        sql = "SELECT chunk_id, doc_title, category, heading, content, filepath FROM knowledge_chunks"
        params: list = []
        if category and isinstance(category, str):
            sql += " WHERE category = ?"
            params.append(category)

        with self.manager.get_connection() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()

        if not rows:
            return []

        scored_results: list[SearchResult] = []

        for r in rows:
            doc_title = r["doc_title"]
            cat = r["category"]
            heading = r["heading"]
            content = r["content"]
            filepath = r["filepath"]
            chunk_id = r["chunk_id"]

            norm_heading = self.normalize_text(heading)
            norm_content = self.normalize_text(content)
            norm_title = self.normalize_text(doc_title)

            score = 0.0

            # 1. Exact phrase match
            if clean_q in norm_content:
                score += 5.0
            if clean_q in norm_heading:
                score += 8.0
            if clean_q in norm_title:
                score += 10.0

            # 2. Token match coverage
            content_tokens = set(self.tokenize(content))
            heading_tokens = set(self.tokenize(heading))
            title_tokens = set(self.tokenize(doc_title))

            matched_in_content = 0
            for t in q_tokens:
                if t in content_tokens:
                    score += 1.2
                    matched_in_content += 1
                if t in heading_tokens:
                    score += 2.5
                if t in title_tokens:
                    score += 3.0

            # Penalize if few query tokens matched
            token_coverage = matched_in_content / max(len(q_tokens), 1)
            score *= (0.5 + 0.5 * token_coverage)

            if score > 0.8:
                # Extract snippet around best matching term
                snippet = self._extract_snippet(content, q_tokens)
                scored_results.append(SearchResult(
                    doc_title=doc_title,
                    category=cat,
                    heading=heading,
                    snippet=snippet,
                    score=round(score, 2),
                    filepath=filepath,
                    chunk_id=chunk_id
                ))

        # Sort descending by score
        scored_results.sort(key=lambda x: x.score, reverse=True)
        return scored_results[:limit]

    def _extract_snippet(self, content: str, q_tokens: list[str], max_len: int = 240) -> str:
        """Extract a readable excerpt centered around matching terms."""
        lines = content.splitlines()
        norm_lines = [self.normalize_text(line) for line in lines]

        best_line_idx = 0
        best_line_matches = -1

        for idx, nline in enumerate(norm_lines):
            matches = sum(1 for t in q_tokens if t in nline)
            if matches > best_line_matches:
                best_line_matches = matches
                best_line_idx = idx

        # Extract surrounding context
        start = max(0, best_line_idx - 1)
        end = min(len(lines), best_line_idx + 3)
        snippet_text = " ".join([l.strip() for l in lines[start:end] if l.strip()])

        if len(snippet_text) > max_len:
            snippet_text = snippet_text[:max_len] + "..."

        return snippet_text

    def get_relevant_context(self, query: str, limit: int = 3, max_chars: int = 1500) -> str:
        """Format top search results as a formatted Persian context block for LLM/Agent reasoning."""
        results = self.search(query, limit=limit)
        if not results:
            return ""

        context_parts = ["### اطلاعات تخصصی استخراج‌شده از مستندات پایگاه دانش:"]
        current_len = 0

        for r in results:
            part = f"- **{r.doc_title}** [{r.heading}]:\n  {r.snippet}"
            if current_len + len(part) > max_chars:
                break
            context_parts.append(part)
            current_len += len(part)

        return "\n\n".join(context_parts)


# Singleton instance
knowledge_search_engine = KnowledgeSearchEngine()
