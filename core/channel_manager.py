"""
Módulo de Gerenciamento Estratégico dos 20 Canais de YouTube.
Controla identidade, linha editorial, limites diários de postagem e cotas.
"""
import sqlite3
from typing import List, Dict, Any, Optional

from database.db import get_db_connection

class ChannelManager:
    def __init__(self):
        pass

    def list_all_channels(self) -> List[Dict[str, Any]]:
        """Retorna todos os 20 canais com métricas consolidadas."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, 
                       (SELECT COUNT(*) FROM scripts s WHERE s.channel_id = c.id) as total_scripts,
                       (SELECT COUNT(*) FROM publications p WHERE p.channel_id = c.id) as total_published
                FROM channels c
                ORDER BY c.channel_number ASC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_channel_by_id(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """Recupera detalhes estratégicos de um canal específico."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM channels WHERE id = ? OR channel_number = ?", (channel_id, channel_id))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_channel_strategy(
        self,
        channel_id: int,
        name: Optional[str] = None,
        niche: Optional[str] = None,
        target_audience: Optional[str] = None,
        editing_style: Optional[str] = None,
        communication_tone: Optional[str] = None,
        editorial_strategy: Optional[str] = None,
        posting_frequency: Optional[str] = None,
        status: Optional[str] = None
    ) -> bool:
        """Atualiza a identidade e estratégia editorial de um canal."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE channels SET
                    name = COALESCE(?, name),
                    niche = COALESCE(?, niche),
                    target_audience = COALESCE(?, target_audience),
                    editing_style = COALESCE(?, editing_style),
                    communication_tone = COALESCE(?, communication_tone),
                    editorial_strategy = COALESCE(?, editorial_strategy),
                    posting_frequency = COALESCE(?, posting_frequency),
                    status = COALESCE(?, status)
                WHERE id = ? OR channel_number = ?
            """, (name, niche, target_audience, editing_style, communication_tone, 
                  editorial_strategy, posting_frequency, status, channel_id, channel_id))
            conn.commit()
            return cursor.rowcount > 0
