"""
Laboratório de Experimentos A/B e Aprendizado Contínuo.
Testa hipóteses editoriais, compara variantes de ganchos e retroalimenta o Grafo de Conhecimento Central.
"""
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from memory.central_memory import CentralMemory

class ExperimentationLab:
    def __init__(self, memory: Optional[CentralMemory] = None):
        self.memory = memory or CentralMemory()

    def create_experiment(self, title: str, hypothesis: str, variable_type: str,
                          control_variant: str, test_variant: str,
                          channel_id: int) -> int:
        """
        Cria um novo experimento A/B:
        variable_type pode ser: 'hook_style', 'editorial_profile', 'pacing_bpm', 'visual_variant'
        """
        with self.memory._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO experiments (
                    title, hypothesis, variable_type, control_variant,
                    test_variant, channel_id, status
                ) VALUES (?, ?, ?, ?, ?, ?, 'running')
            """, (title, hypothesis, variable_type, control_variant, test_variant, channel_id))
            conn.commit()
            return cursor.lastrowid

    def record_experiment_results(self, experiment_id: int,
                                  control_metrics: Dict[str, Any],
                                  test_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Registra os resultados reais de métricas (views, retenção %, curtidas) de ambas as variantes.
        Determina a variante vencedora e registra os aprendizados na Central Memory.
        """
        c_ret = float(control_metrics.get("retention_rate", 60.0))
        t_ret = float(test_metrics.get("retention_rate", 60.0))
        
        winner = "test" if t_ret > c_ret else "control"
        gain_percent = round(abs(t_ret - c_ret), 2)
        
        insights = f"Variante {winner.upper()} venceu com {gain_percent}% de vantagem na taxa de retenção média."

        with self.memory._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE experiments SET
                    metrics_control = ?,
                    metrics_test = ?,
                    status = 'concluded',
                    winner = ?,
                    insights_learned = ?,
                    concluded_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                json.dumps(control_metrics, ensure_ascii=False),
                json.dumps(test_metrics, ensure_ascii=False),
                winner, insights, experiment_id
            ))
            conn.commit()

        # Retroalimenta os nós de conhecimento da Inteligência Central
        self.memory.record_knowledge_node(
            category_slug="geral",
            node_type="experiment_learning",
            title=f"Aprendizado A/B: {winner.upper()} superou por {gain_percent}%",
            pattern_data={
                "experiment_id": experiment_id,
                "winner": winner,
                "control_metrics": control_metrics,
                "test_metrics": test_metrics,
                "insights": insights
            },
            effectiveness_score=max(60.0, min(99.0, max(c_ret, t_ret)))
        )

        return {
            "experiment_id": experiment_id,
            "winner": winner,
            "gain_percent": gain_percent,
            "insights": insights
        }

    def list_experiments(self) -> List[Dict[str, Any]]:
        with self.memory._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM experiments ORDER BY id DESC")
            rows = [dict(r) for r in cursor.fetchall()]
            for r in rows:
                for f in ["metrics_control", "metrics_test"]:
                    if r.get(f):
                        try:
                            r[f] = json.loads(r[f])
                        except Exception:
                            pass
            return rows
