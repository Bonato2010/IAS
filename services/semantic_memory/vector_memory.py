"""
IAS Semantic Memory Service
Busca vetorial por significado e contexto para transcrições, ganchos e padrões de retenção.
Compatível com pgvector (PostgreSQL) e fallback local em Numpy + SQLite.
"""
import os
import re
import json
import sqlite3
import hashlib
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

from .pgvector_adapter import PgVectorAdapter

class VectorMemoryService:
    """Serviço de Memória Semântica com busca vetorial de alta velocidade."""

    def __init__(self, db_path: Optional[str] = None):
        if not db_path:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.db_path = str(base_dir / "database" / "shorts_central.db")
        else:
            self.db_path = db_path

        self.pg_adapter = PgVectorAdapter()
        self._init_sqlite_tables()

    def _init_sqlite_tables(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS semantic_vectors (
                    id TEXT PRIMARY KEY,
                    category TEXT,
                    text_content TEXT,
                    vector_blob BLOB,
                    metadata_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vec_cat ON semantic_vectors(category)")
            conn.commit()

    def generate_embedding(self, text: str, dim: int = 384) -> np.ndarray:
        """
        Gera um vetor normalizado de 384 dimensões para representação semântica.
        Usa tokenização de n-gramas + projeção hash densa L2 normalizada,
        garantindo consistência determinística sem depender de modelos de 5 GB para testes.
        """
        if not text:
            return np.zeros(dim, dtype=np.float32)

        # Tokenização limpa
        tokens = re.findall(r"\b\w{2,}\b", text.lower())
        vec = np.zeros(dim, dtype=np.float32)

        for i, token in enumerate(tokens):
            # Gera múltiplas projeções por termo (unigrama e bigrama)
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if ((h >> 8) % 2 == 0) else -1.0
            weight = 1.0 / (1.0 + (i * 0.05)) # Leve ênfase no início do texto (gancho)
            vec[idx] += sign * weight

            if i < len(tokens) - 1:
                bigram = f"{token}_{tokens[i+1]}"
                h_bi = int(hashlib.md5(bigram.encode("utf-8")).hexdigest(), 16)
                idx_bi = h_bi % dim
                sign_bi = 1.0 if ((h_bi >> 8) % 2 == 0) else -1.0
                vec[idx_bi] += sign_bi * 1.5 # Bigramas têm maior peso contextual

        # Normalização L2 para cálculo de similaridade de cosseno direto via dot product
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.astype(np.float32)

    def index_item(self, item_id: str, text: str, category: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Indexa um item na memória semântica vetorial."""
        vec = self.generate_embedding(text)
        meta_str = json.dumps(metadata or {}, ensure_ascii=False)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO semantic_vectors (id, category, text_content, vector_blob, metadata_json)
                VALUES (?, ?, ?, ?, ?)
            """, (item_id, category, text, vec.tobytes(), meta_str))
            conn.commit()
        return True

    def search_similar(self, query: str, category: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """Busca os itens mais semanticamente similares usando distância de cosseno."""
        # Se pgvector estiver disponível no PostgreSQL, consulta por ele
        if self.pg_adapter.is_available():
            q_vec = self.generate_embedding(query).tolist()
            pg_res = self.pg_adapter.query_similarity("semantic_transcriptions", q_vec, top_k)
            if pg_res:
                return pg_res

        # Fallback local via Numpy + SQLite
        q_vec = self.generate_embedding(query)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute("SELECT id, category, text_content, vector_blob, metadata_json FROM semantic_vectors WHERE category = ?", (category,))
            else:
                cursor.execute("SELECT id, category, text_content, vector_blob, metadata_json FROM semantic_vectors")
            rows = cursor.fetchall()

        if not rows:
            return []

        scored = []
        for r in rows:
            item_id, cat, text, blob, meta_json = r
            if not blob:
                continue
            item_vec = np.frombuffer(blob, dtype=np.float32)
            # Dot product de vetores unitários = Cosine Similarity
            sim = float(np.dot(q_vec, item_vec))
            scored.append({
                "id": item_id,
                "category": cat,
                "text": text,
                "metadata": json.loads(meta_json or "{}"),
                "similarity_score": round(max(0.0, min(1.0, (sim + 1.0) / 2.0)), 4)
            })

        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored[:top_k]

    def index_hook(self, hook_id: str, hook_text: str, retention_score: float, niche: str) -> bool:
        return self.index_item(
            item_id=hook_id,
            text=hook_text,
            category="hook",
            metadata={"retention_score": retention_score, "niche": niche}
        )

    def search_hooks(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        return self.search_similar(query=query, category="hook", top_k=top_k)

    def get_stats(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT category, COUNT(*) FROM semantic_vectors GROUP BY category")
            rows = cursor.fetchall()
            return {
                "total_indexed": sum(r[1] for r in rows),
                "by_category": dict(rows),
                "backend": "PostgreSQL (pgvector)" if self.pg_adapter.is_available() else "Local SQLite (Numpy Cosine Vector Engine)",
                "embedding_dimension": 384
            }
