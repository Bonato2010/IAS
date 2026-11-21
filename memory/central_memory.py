"""
Central Memory & Knowledge Base
Gerencia a inteligência compartilhada, nós de conhecimento, padrões virais e memória de longo prazo.
"""
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database/shorts_central.db"

class CentralMemory:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = str(db_path or DB_PATH)

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # --- Padrões de Conteúdo (Viral Patterns) ---
    def record_pattern(self, category_slug: str, pattern_type: str, title: str,
                       structure_template: str, hook_formula: str = "",
                       ideal_duration: float = 45.0, typical_retention: float = 75.0,
                       source_ref_id: Optional[int] = None, metadata: Optional[Dict] = None) -> int:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM categories WHERE slug = ?", (category_slug,))
            row = cursor.fetchone()
            cat_id = row["id"] if row else 1

            cursor.execute("""
                INSERT INTO content_patterns (
                    category_id, archetype, hook_type, pattern_type, title, structure_template,
                    hook_formula, ideal_duration_seconds, typical_retention_rate,
                    source_reference_id, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cat_id, category_slug, pattern_type, pattern_type, title, structure_template,
                hook_formula, ideal_duration, typical_retention,
                source_ref_id, json.dumps(metadata or {}, ensure_ascii=False)
            ))
            conn.commit()
            return cursor.lastrowid

    def query_patterns(self, category_slug: Optional[str] = None, pattern_type: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            query = """
                SELECT cp.*, c.slug as category_slug, c.name as category_name
                FROM content_patterns cp
                LEFT JOIN categories c ON cp.category_id = c.id
                WHERE 1=1
            """
            params = []
            if category_slug:
                query += " AND c.slug = ?"
                params.append(category_slug)
            if pattern_type:
                query += " AND (cp.pattern_type = ? OR cp.hook_type = ?)"
                params.extend([pattern_type, pattern_type])
            query += " ORDER BY cp.typical_retention_rate DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    # --- Grafo de Nós de Conhecimento (Knowledge Nodes) ---
    def record_knowledge_node(self, category_slug: str, node_type: str, title: str,
                              pattern_data: Dict[str, Any], effectiveness_score: float = 60.0,
                              derived_from: Optional[List[str]] = None) -> int:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO knowledge_nodes (
                    category_slug, node_type, title, pattern_data,
                    effectiveness_score, derived_from_references
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                category_slug, node_type, title,
                json.dumps(pattern_data, ensure_ascii=False),
                effectiveness_score,
                json.dumps(derived_from or [], ensure_ascii=False)
            ))
            conn.commit()
            return cursor.lastrowid

    def query_knowledge_nodes(self, node_type: Optional[str] = None, category_slug: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM knowledge_nodes WHERE 1=1"
            params = []
            if node_type:
                query += " AND node_type = ?"
                params.append(node_type)
            if category_slug:
                query += " AND category_slug = ?"
                params.append(category_slug)
            query += " ORDER BY effectiveness_score DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            nodes = []
            for r in cursor.fetchall():
                d = dict(r)
                try:
                    d["pattern_data"] = json.loads(d["pattern_data"])
                except Exception:
                    pass
                nodes.append(d)
            return nodes

    # --- Decisões e Deliberações dos Agentes ---
    def log_agent_decision(self, agent_name: str, target_type: str, target_id: Optional[int],
                           input_data: Dict[str, Any], analysis: Dict[str, Any],
                           score: int, confidence: float, recommendation: str) -> int:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO agent_decisions (
                    agent_name, target_type, target_id, input_data,
                    analysis, score, confidence, recommendation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_name, target_type, target_id,
                json.dumps(input_data, ensure_ascii=False),
                json.dumps(analysis, ensure_ascii=False),
                score, confidence, recommendation
            ))
            conn.commit()
            return cursor.lastrowid

    def get_agent_history(self, agent_name: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM agent_decisions"
            params = []
            if agent_name:
                query += " WHERE agent_name = ?"
                params.append(agent_name)
            query += " ORDER BY id DESC LIMIT ?"
            params.append(limit)
            cursor.execute(query, params)
            results = []
            for r in cursor.fetchall():
                d = dict(r)
                for f in ["input_data", "analysis"]:
                    if d.get(f):
                        try:
                            d[f] = json.loads(d[f])
                        except Exception:
                            pass
                results.append(d)
            return results

    # --- Estatísticas Globais da Inteligência Central ---
    def get_summary_stats(self) -> Dict[str, Any]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            stats = {}
            cursor.execute("SELECT COUNT(*) FROM video_references")
            stats["total_references"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM content_patterns")
            stats["total_patterns"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM knowledge_nodes")
            stats["total_knowledge_nodes"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM agent_decisions")
            stats["total_agent_decisions"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM podcast_candidate_cuts")
            stats["total_podcast_cuts"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM channels")
            stats["total_channels"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM editorial_profiles")
            stats["total_profiles"] = cursor.fetchone()[0]
            return stats
