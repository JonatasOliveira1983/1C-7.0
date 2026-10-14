# -*- coding: utf-8 -*-
"""
1CRYPTEN 7.0 — Semantic Knowledge RAG Service (Second Brain & Architecture)
Provides sub-millisecond indexed retrieval across:
- MASTER_ARCHITECTURE.md (Canonical architecture & invariants)
- vault_galaxy/ (Obsidian Vault: journal, trades, strategies)
- .agents/rules/ (Superpowers methodology & AGENTS.md)
"""
import os
import re
import math
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("1CRYPTEN-RAG")


class KnowledgeChunk:
    def __init__(self, chunk_id: str, title: str, content: str, source: str, category: str):
        self.chunk_id = chunk_id
        self.title = title
        self.content = content
        self.source = source
        self.category = category
        self.tokens = self._tokenize(f"{title} {content}")
        self.term_freq = self._calculate_tf()

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        cleaned = re.sub(r"[^\w\s-]", " ", text.lower())
        tokens = [w for w in cleaned.split() if len(w) > 2]
        return tokens

    def _calculate_tf(self) -> Dict[str, float]:
        tf: Dict[str, float] = {}
        total = len(self.tokens)
        if total == 0:
            return tf
        for t in self.tokens:
            tf[t] = tf.get(t, 0.0) + 1.0
        for t in tf:
            tf[t] = tf[t] / total
        return tf


class RAGService:
    def __init__(self, root_dir: Optional[str] = None):
        if root_dir is None:
            # Assume backend is running from repo root or backend/
            base = Path(__file__).resolve().parent.parent.parent
            self.root_dir = base
        else:
            self.root_dir = Path(root_dir)

        self.chunks: List[KnowledgeChunk] = []
        self.doc_freq: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.total_docs: int = 0
        self.last_indexed_at: float = 0.0
        self.is_indexed: bool = False

    def index_all(self) -> Dict[str, Any]:
        """Indexes all knowledge sources: MASTER_ARCHITECTURE.md, vault_galaxy, .agents/rules."""
        t0 = time.time()
        new_chunks: List[KnowledgeChunk] = []

        # 1. Index MASTER_ARCHITECTURE.md
        arch_path = self.root_dir / "MASTER_ARCHITECTURE.md"
        if arch_path.exists():
            new_chunks.extend(self._chunk_markdown(arch_path, category="ARCHITECTURE"))

        # 2. Index vault_galaxy
        vault_path = self.root_dir / "vault_galaxy"
        if vault_path.exists():
            for md_file in vault_path.glob("**/*.md"):
                sub_cat = md_file.parent.name.upper()
                new_chunks.extend(self._chunk_markdown(md_file, category=f"GALAXY_{sub_cat}"))

        # 3. Index .agents/rules and AGENTS.md
        agents_md = self.root_dir / "AGENTS.md"
        if agents_md.exists():
            new_chunks.extend(self._chunk_markdown(agents_md, category="METHODOLOGY"))

        rules_dir = self.root_dir / ".agents" / "rules"
        if rules_dir.exists():
            for md_file in rules_dir.glob("*.md"):
                new_chunks.extend(self._chunk_markdown(md_file, category="RULES"))

        # 4. Index docs/ directory (Audits, blueprints, technical specs)
        docs_dir = self.root_dir / "docs"
        if docs_dir.exists():
            for md_file in docs_dir.glob("**/*.md"):
                new_chunks.extend(self._chunk_markdown(md_file, category="DOCS"))

        self.chunks = new_chunks
        self.total_docs = len(self.chunks)
        self._calculate_idf()
        self.last_indexed_at = time.time()
        self.is_indexed = True

        elapsed_ms = round((time.time() - t0) * 1000, 1)
        logger.info(f"[RAG] Indexados {self.total_docs} chunks de conhecimento em {elapsed_ms}ms.")
        return {
            "status": "success",
            "total_chunks": self.total_docs,
            "indexed_in_ms": elapsed_ms,
            "timestamp": self.last_indexed_at
        }

    def _chunk_markdown(self, file_path: Path, category: str) -> List[KnowledgeChunk]:
        """Splits markdown file into coherent sections based on headers."""
        chunks: List[KnowledgeChunk] = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"⚠️ [RAG] Erro ao ler {file_path}: {e}")
            return chunks

        rel_path = str(file_path.relative_to(self.root_dir))
        sections = re.split(r"\n(?=#{1,3}\s)", content)

        for i, sec in enumerate(sections):
            text = sec.strip()
            if len(text) < 50:
                continue

            # Extract header as title if available
            lines = text.split("\n")
            first_line = lines[0].strip()
            title = re.sub(r"^#{1,3}\s*", "", first_line) if first_line.startswith("#") else f"{file_path.stem} Parte {i+1}"
            
            chunk_id = f"{rel_path}:{i+1}"
            chunks.append(KnowledgeChunk(
                chunk_id=chunk_id,
                title=title,
                content=text,
                source=rel_path,
                category=category
            ))

        return chunks

    def _calculate_idf(self):
        """Calculates Inverse Document Frequency for BM25/TF-IDF scoring."""
        self.doc_freq.clear()
        self.idf.clear()
        for chunk in self.chunks:
            unique_terms = set(chunk.tokens)
            for t in unique_terms:
                self.doc_freq[t] = self.doc_freq.get(t, 0) + 1

        for term, df in self.doc_freq.items():
            self.idf[term] = math.log((self.total_docs + 1) / (df + 1)) + 1.0

    def search(self, query: str, top_k: int = 4, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns the top_k most relevant knowledge chunks for a given query."""
        if not self.is_indexed:
            self.index_all()

        query_tokens = KnowledgeChunk._tokenize(query)
        if not query_tokens:
            return []

        scored_chunks: List[tuple] = []
        for chunk in self.chunks:
            if category and not chunk.category.startswith(category):
                continue

            score = 0.0
            for qt in query_tokens:
                if qt in chunk.term_freq:
                    tf = chunk.term_freq[qt]
                    idf = self.idf.get(qt, 1.0)
                    score += tf * idf

            # Boost exact title match
            title_lower = chunk.title.lower()
            if any(qt in title_lower for qt in query_tokens):
                score += 1.5

            if score > 0.0:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, ch in scored_chunks[:top_k]:
            results.append({
                "chunk_id": ch.chunk_id,
                "title": ch.title,
                "category": ch.category,
                "source": ch.source,
                "relevance_score": round(score, 4),
                "snippet": ch.content[:800],
                "content": ch.content
            })

        return results

    def format_context_for_prompt(self, query: str, top_k: int = 3, max_chars: int = 3000) -> str:
        """Retrieves and formats context snippets ready to be injected into LLM/Hermes prompt."""
        results = self.search(query, top_k=top_k)
        if not results:
            return ""

        context_lines = ["\n[SEGUNDO CEREBRO — CONTEXTO RAG RELEVANTE]"]
        total_len = 0
        for r in results:
            entry = f"\n--- [{r['category']}] {r['title']} ({r['source']}) ---\n{r['snippet']}\n"
            if total_len + len(entry) > max_chars:
                break
            context_lines.append(entry)
            total_len += len(entry)

        return "\n".join(context_lines)


# Singleton
rag_service = RAGService()
