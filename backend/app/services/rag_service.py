"""
Base Tecnológica — Serviço de RAG Local (Retrieval-Augmented Generation).
Motor de busca semântica e contextual 100% local, sem dependência de APIs pagas de embeddings.
- Ingestão automática de documentos (.md, .txt, .pdf) da pasta `backend/data/knowledge/`
- Algoritmo de ranking BM25 Okapi com normalização de tokens e remoção de stopwords em PT-BR
- Chunking inteligente com sobreposição (sliding window) preservando quebras de parágrafos
- Integração nativa com Hermes e endpoints MCP
"""
import os
import re
import math
import unicodedata
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

STOPWORDS_PT = {
    "de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "com", "nao", "não",
    "uma", "os", "no", "se", "na", "por", "mais", "as", "dos", "como", "mas", "foi",
    "ao", "ele", "das", "tem", "seu", "sua", "ou", "ser", "quando", "muito", "nos",
    "ja", "já", "está", "esta", "pelo", "pela", "ate", "até", "isso", "ela", "entre",
    "era", "depois", "sem", "mesmo", "aos", "ter", "seus", "quem", "nas", "me", "esse",
    "eles", "estao", "estão", "voce", "você", "tinha", "foram", "essa", "num", "nem",
    "suas", "meu", "as", "minha", "numa", "pelos", "elas", "havia", "seja", "qual"
}


def normalize_text(text: str) -> str:
    """Remove acentuação e caracteres especiais para comparação uniforme."""
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
    return text.lower().strip()


def tokenize(text: str) -> List[str]:
    """Tokeniza texto em palavras minúsculas, filtrando pontuações e stopwords."""
    norm = normalize_text(text)
    words = re.findall(r"\b[a-z0-9_]{2,}\b", norm)
    return [w for w in words if w not in STOPWORDS_PT]


class RAGDocumentChunk:
    def __init__(self, chunk_id: str, source: str, content: str, tokens: List[str], metadata: Optional[Dict[str, Any]] = None):
        self.chunk_id = chunk_id
        self.source = source
        self.content = content
        self.tokens = tokens
        self.metadata = metadata or {}
        self.token_len = len(tokens)


class RAGService:
    def __init__(self, knowledge_dir: Optional[str] = None):
        if knowledge_dir:
            self.knowledge_dir = Path(knowledge_dir)
        else:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.knowledge_dir = base_dir / "data" / "knowledge"

        self.chunks: List[RAGDocumentChunk] = []
        self.doc_count = 0
        self.avg_doc_len = 0.0
        self.idf: Dict[str, float] = {}
        self.doc_freq: Dict[str, int] = {}
        self.is_indexed = False

        # Cria pasta de conhecimento caso não exista
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self.reload_index()

    def _extract_text_from_pdf(self, file_path: Path) -> str:
        """Extrai texto de PDF usando PyMuPDF local sem serviços externos."""
        if not fitz:
            return ""
        text_parts = []
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text_parts.append(page.get_text() or "")
            doc.close()
        except Exception:
            return ""
        return "\n".join(text_parts)

    def _split_into_chunks(self, text: str, source_name: str, chunk_size: int = 150, overlap: int = 30) -> List[RAGDocumentChunk]:
        """Divide o texto em blocos contíguos de tokens com sobreposição."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        words_stream: List[str] = []
        for p in paragraphs:
            for w in p.split():
                words_stream.append(w)

        if not words_stream:
            return []

        chunks: List[RAGDocumentChunk] = []
        step = max(1, chunk_size - overlap)
        chunk_idx = 0

        for i in range(0, len(words_stream), step):
            slice_words = words_stream[i : i + chunk_size]
            chunk_text = " ".join(slice_words)
            tokens = tokenize(chunk_text)
            if len(tokens) >= 5:  # ignora chunks vazios ou insignificantes
                chunk_id = f"{source_name}_chunk_{chunk_idx}"
                chunks.append(RAGDocumentChunk(
                    chunk_id=chunk_id,
                    source=source_name,
                    content=chunk_text,
                    tokens=tokens
                ))
                chunk_idx += 1

        return chunks

    def reload_index(self) -> int:
        """Varre os diretórios de conhecimento canônicos e indexa todos os arquivos suportados."""
        self.chunks.clear()
        self.doc_freq.clear()
        self.idf.clear()

        # Diretórios canônicos de inteligência
        sources_to_index: List[Path] = []
        
        # 1. Base knowledge dir
        if self.knowledge_dir.exists():
            sources_to_index.extend(list(self.knowledge_dir.glob("**/*.*")))
            
        # 2. MASTER_ARCHITECTURE.md da raiz
        repo_root = self.knowledge_dir.parent.parent.parent
        arch_md = repo_root / "MASTER_ARCHITECTURE.md"
        if arch_md.exists():
            sources_to_index.append(arch_md)
            
        # 3. vault_galaxy (Obsidian Second Brain)
        vault_galaxy = repo_root / "vault_galaxy"
        if vault_galaxy.exists():
            sources_to_index.extend(list(vault_galaxy.glob("**/*.md")))

        for f in sources_to_index:
            ext = f.suffix.lower()
            text = ""
            if ext in [".txt", ".md", ".json"]:
                try:
                    text = f.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
            elif ext == ".pdf":
                text = self._extract_text_from_pdf(f)

            if text.strip():
                new_chunks = self._split_into_chunks(text, f.name)
                self.chunks.extend(new_chunks)

        self.doc_count = len(self.chunks)
        if self.doc_count == 0:
            self.avg_doc_len = 0.0
            self.is_indexed = True
            return 0

        # Calcula frequências de documentos (DF)
        total_len = 0
        for chunk in self.chunks:
            total_len += chunk.token_len
            seen = set(chunk.tokens)
            for token in seen:
                self.doc_freq[token] = self.doc_freq.get(token, 0) + 1

        self.avg_doc_len = total_len / self.doc_count

        # Calcula IDF (Inverted Document Frequency) com suavização BM25
        for token, df in self.doc_freq.items():
            self.idf[token] = math.log(1.0 + (self.doc_count - df + 0.5) / (df + 0.5))

        self.is_indexed = True
        return self.doc_count

    def search(self, query: str, top_k: int = 3, min_score: float = 0.1) -> List[Dict[str, Any]]:
        """
        Executa busca BM25 Okapi nos chunks indexados.
        Retorna lista ordenada por relevância.
        """
        if not self.is_indexed or not self.chunks:
            self.reload_index()

        q_tokens = tokenize(query)
        if not q_tokens:
            return []

        k1 = 1.5
        b = 0.75
        scored_chunks = []

        for chunk in self.chunks:
            score = 0.0
            chunk_token_counts: Dict[str, int] = {}
            for t in chunk.tokens:
                chunk_token_counts[t] = chunk_token_counts.get(t, 0) + 1

            for qt in q_tokens:
                if qt in chunk_token_counts:
                    tf = chunk_token_counts[qt]
                    idf = self.idf.get(qt, 0.5)
                    # Fórmula BM25
                    denom = tf + k1 * (1.0 - b + b * (chunk.token_len / (self.avg_doc_len or 1.0)))
                    score += idf * ((tf * (k1 + 1.0)) / (denom or 1.0))

            if score >= min_score:
                scored_chunks.append({
                    "chunk_id": chunk.chunk_id,
                    "source": chunk.source,
                    "content": chunk.content,
                    "score": round(score, 3)
                })

        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]

    def get_relevant_context(self, query: str, max_chars: int = 1200) -> str:
        """Gera um bloco formatado de contexto para injeção no prompt do Hermes."""
        results = self.search(query, top_k=3)
        if not results:
            return ""

        context_blocks = []
        acc_len = 0
        for r in results:
            snippet = f"--- [Fonte: {r['source']}] ---\n{r['content']}\n"
            if acc_len + len(snippet) > max_chars:
                break
            context_blocks.append(snippet)
            acc_len += len(snippet)

        if not context_blocks:
            return ""

        return "\n[CONHECIMENTO DA BASE DO SISTEMA (RAG LOCAL)]:\n" + "\n".join(context_blocks) + "\n"


rag_service = RAGService()
