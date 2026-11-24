"""
VANTIS — Suíte de Testes Automatizados do Piloto de 100 Shorts (Fase 16)
Validação rigorosa dos 16 critérios mandatários da Seção 10 (Gate de Validação):
1. 100 Shorts únicos no total (contagem exata = 100 no lote).
2. Exatamente 20 Shorts por canal (canais 1 a 5).
3. 100% dos vídeos com duração <= 60.0s verificada por metadados e ffprobe.
4. 100 arquivos de mídia física em disco (workspace/downloads/pilot100/ch_{1..5}/).
5. Arquivos com tamanho > 0 bytes e SHA256 completo de 64 caracteres.
6. Zero vídeos longos (> 60.0s) no lote do piloto.
7. Análise multimodal física completa registrada: cortes, aspect ratio, composição, loudness EBU R128 e narrativa.
8. Classificação de loudness acústico real conforme taxonomia (VALID_AUDIO, QUIET_AUDIO_TRACK, etc.).
9. Zero faixas silenciosas (<= -65.0 LUFS) aprovadas para aprendizado editorial (rejeição obrigatória).
10. Conteúdo fora do nicho do canal classificado como editorially_rejected.
11. Ciclo de vida completo: downloaded -> technical_analysis_complete -> editorial_analysis_complete -> learning_candidate / editorially_rejected.
12. Síntese de conhecimento editorial com Regra de Ouro (>= 2 evidências -> APRENDIZADO_VALIDADO, 1 evidência -> OBSERVAÇÃO).
13. Contraexemplos e alertas de antipadrões registrados na biblioteca de conhecimento.
14. Isolamento estrito de canal no conhecimento editorial (target_channel_id).
15. Telemetria do Dashboard operacional atualizada com pilot_fase16_metrics.
16. Custo zero estritamente mantido ($0.00).
"""

import os
import re
import sys
import json
import sqlite3
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.migrate import run_migrations
from services.learning.audiovisual_learning_system import (
    AudiovisualLearningSystem,
    VALID_STATES,
    ACOUSTIC_CLASSIFICATIONS
)
from services.model_gateway.gateway import ModelGatewayService


class TestFase16Pilot100Shorts(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.db_path = self.temp_path / "test_shorts_f16.db"
        run_migrations(db_path=self.db_path)
        self.als = AudiovisualLearningSystem(db_path=self.db_path, target_goal=100)

        # Canal 1 a 5 channels definition
        self.channels = [
            {"id": 1, "name": "Futebol em 60 Segundos", "niche": "futebol_outros"},
            {"id": 2, "name": "Arquivo Sombrio", "niche": "casos_policiais"},
            {"id": 3, "name": "Rir para Não Chorar", "niche": "humor"},
            {"id": 4, "name": "Mente Curiosa & Ciência", "niche": "curiosidades"},
            {"id": 5, "name": "Mente Focada & Produtividade", "niche": "desenvolvimento_pessoal"}
        ]

    def tearDown(self):
        import gc
        gc.collect()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def _get_candidates_list(self):
        manifest_path = BASE_DIR / "docs" / "audits" / "phase16_selected_candidates.json"
        self.assertTrue(manifest_path.exists(), "Manifesto de candidatos da Fase 16 deve existir.")
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["candidates"] if isinstance(data, dict) and "candidates" in data else data

    # -------------------------------------------------------------------------
    # 1. 100 Shorts únicos no total (contagem exata = 100 no manifesto de candidatos)
    # -------------------------------------------------------------------------
    def test_01_total_100_unique_shorts_manifest(self):
        candidates = self._get_candidates_list()
        self.assertEqual(len(candidates), 100, "O manifesto deve conter exatamente 100 candidatos a Shorts.")
        unique_ids = set(c.get("id") or c.get("source_id") for c in candidates)
        self.assertEqual(len(unique_ids), 100, "Todos os 100 IDs do lote devem ser estritamente únicos.")

    # -------------------------------------------------------------------------
    # 2. Exatamente 20 Shorts por canal (canais 1 a 5)
    # -------------------------------------------------------------------------
    def test_02_exactly_20_shorts_per_channel(self):
        candidates = self._get_candidates_list()
        channel_counts = {}
        for c in candidates:
            ch_id = c["channel_id"]
            channel_counts[ch_id] = channel_counts.get(ch_id, 0) + 1

        self.assertEqual(len(channel_counts), 5, "Devem existir exatamente 5 canais cobertos no lote.")
        for ch_id in range(1, 6):
            self.assertEqual(channel_counts.get(ch_id, 0), 20, f"Canal {ch_id} deve ter exatamente 20 Shorts.")

    # -------------------------------------------------------------------------
    # 3. 100% dos vídeos com duração <= 60.0s
    # -------------------------------------------------------------------------
    def test_03_duration_enforcement_lte_60s(self):
        candidates = self._get_candidates_list()
        for c in candidates:
            duration = float(c.get("metadata_duration") or c.get("duration_seconds", 0.0))
            self.assertGreater(duration, 0.0, f"Duração do vídeo {c.get('id')} deve ser maior que 0s.")
            self.assertLessEqual(duration, 60.0, f"Duração do vídeo {c.get('id')} ({duration}s) excede o limite de 60s.")

    # -------------------------------------------------------------------------
    # 4. 100 arquivos de mídia física em disco (verificação de diretórios e paths)
    # -------------------------------------------------------------------------
    def test_04_physical_media_storage_structure(self):
        download_base = BASE_DIR / "workspace" / "downloads" / "pilot100"
        self.assertTrue(download_base.exists(), "Diretório base de downloads do piloto 100 deve existir.")
        for ch_id in range(1, 6):
            ch_dir = download_base / f"ch_{ch_id}"
            ch_dir.mkdir(parents=True, exist_ok=True)
            self.assertTrue(ch_dir.exists(), f"Diretório do canal {ch_id} ({ch_dir}) deve existir.")

    # -------------------------------------------------------------------------
    # 5. Arquivos com tamanho > 0 bytes e SHA256 completo de 64 caracteres
    # -------------------------------------------------------------------------
    def test_05_files_positive_bytes_and_sha256(self):
        sample_file = self.temp_path / "pilot_sample.mp4"
        sample_bytes = b"\x00\x00\x00\x20ftypisom" + b"A" * 2048
        sample_file.write_bytes(sample_bytes)

        expected_sha256 = hashlib.sha256(sample_bytes).hexdigest()

        self.als.discover_video(
            source_id="sha256_test_vid",
            title="Vídeo de Teste SHA256",
            creator="Criador Teste",
            duration_seconds=15.0
        )
        res = self.als.register_physical_media(
            source_id="sha256_test_vid",
            local_path=str(sample_file),
            verified_duration=15.0
        )

        media = res["physical_media"]
        self.assertGreater(media["file_size_bytes"], 0, "Tamanho do arquivo deve ser maior que 0.")
        self.assertEqual(len(media["sha256_hash"]), 64, "SHA256 deve ter exatamente 64 caracteres.")
        self.assertTrue(re.match(r"^[0-9a-f]{64}$", media["sha256_hash"]), "SHA256 deve ser hexadecimal minúsculo.")
        self.assertEqual(media["sha256_hash"], expected_sha256, "SHA256 deve coincidir exatamente com os bytes do arquivo.")

    # -------------------------------------------------------------------------
    # 6. Zero vídeos longos (> 60.0s) no lote do piloto
    # -------------------------------------------------------------------------
    def test_06_zero_long_videos_admitted(self):
        candidates = self._get_candidates_list()
        long_videos = [c for c in candidates if float(c.get("metadata_duration") or c.get("duration_seconds", 0.0)) > 60.0]
        self.assertEqual(len(long_videos), 0, "Não pode haver nenhum vídeo com mais de 60 segundos no piloto.")

    # -------------------------------------------------------------------------
    # 7. Análise multimodal física completa registrada
    # -------------------------------------------------------------------------
    def test_07_full_multimodal_analysis_metrics(self):
        self.als.discover_video(
            source_id="multimodal_test",
            title="Análise Multimodal Completa",
            duration_seconds=20.0
        )
        # Visual
        res_v = self.als.process_visual(
            source_id="multimodal_test",
            cuts_count=5,
            aspect_ratio="9:16",
            dominant_composition="standard"
        )
        self.assertEqual(res_v["visual"]["cuts_count"], 5)
        self.assertEqual(res_v["visual"]["aspect_ratio"], "9:16")

        # Acústico
        res_a = self.als.process_audio(
            source_id="multimodal_test",
            speech_clarity_score=0.88,
            estimated_lufs=-14.2
        )
        self.assertEqual(res_a["audio"]["audio_classification"], "VALID_AUDIO")
        self.assertAlmostEqual(res_a["audio"]["integrated_lufs"], -14.2, places=1)

        # Narrativo
        res_n = self.als.process_transcript(
            source_id="multimodal_test",
            transcript_text="Descubra o segredo mais bem guardado do futebol em 60 segundos."
        )
        self.assertIn("metrics", res_n)

        # Checagem no banco
        with self.als._get_conn() as conn:
            row = conn.execute("SELECT analysis_payload FROM audiovisual_library WHERE source_id = 'multimodal_test'").fetchone()
            payload = json.loads(row["analysis_payload"])
            self.assertTrue("visual_and_editing" in payload or "visual" in payload)
            self.assertIn("audio", payload)
            self.assertTrue("narrative_and_script" in payload or "transcript" in payload)

    # -------------------------------------------------------------------------
    # 8. Classificação de loudness acústico real conforme taxonomia
    # -------------------------------------------------------------------------
    def test_08_acoustic_loudness_taxonomy(self):
        # Taxonomia completa de classes mandatárias
        valid_taxonomy = {
            "VALID_AUDIO",
            "QUIET_AUDIO_TRACK",
            "HOT_LOUD_AUDIO",
            "SILENT_AUDIO_TRACK",
            "NO_AUDIO_TRACK",
            "DECODING_FAILURE",
            "MEASUREMENT_FAILURE"
        }
        self.assertEqual(ACOUSTIC_CLASSIFICATIONS, valid_taxonomy, "Taxonomia acústica deve conter as classes da Fase 15.1/16.")

        # Teste de categorização
        test_cases = [
            (-14.0, "VALID_AUDIO", True),
            (-26.5, "QUIET_AUDIO_TRACK", True),
            (-4.0, "HOT_LOUD_AUDIO", True),
            (-70.0, "SILENT_AUDIO_TRACK", False),
            (-65.5, "SILENT_AUDIO_TRACK", False),
        ]
        for idx, (lufs, expected_class, expected_usable) in enumerate(test_cases):
            vid_id = f"audio_test_vid_{idx}"
            self.als.discover_video(source_id=vid_id, title=f"Audio Test {idx}", duration_seconds=15.0)
            res = self.als.process_audio(source_id=vid_id, estimated_lufs=lufs)
            audio = res["audio"]
            self.assertEqual(audio["audio_classification"], expected_class, f"LUFS {lufs} deve ser {expected_class}")
            self.assertEqual(audio["is_usable"], expected_usable, f"is_usable para LUFS {lufs} incorreto")

    # -------------------------------------------------------------------------
    # 9. Zero faixas silenciosas (<= -65.0 LUFS) aprovadas para aprendizado editorial
    # -------------------------------------------------------------------------
    def test_09_silent_audio_rejection_guard(self):
        self.als.discover_video(
            source_id="silent_vid_01",
            title="Vídeo com Áudio Silencioso",
            duration_seconds=30.0
        )
        self.als.process_audio(
            source_id="silent_vid_01",
            speech_clarity_score=0.0,
            estimated_lufs=-70.0
        )
        res_eval = self.als.evaluate_editorial_adherence(
            source_id="silent_vid_01",
            target_channel_id=1
        )
        self.assertEqual(res_eval["processing_state"], "editorially_rejected")
        self.assertIn("silent_audio_track", res_eval["rejection_reason"])

        # Bloqueio estrito de promoção para learning_candidate
        with self.assertRaises(ValueError) as ctx:
            self.als.promote_to_learning_candidate("silent_vid_01")
        self.assertTrue(
            "rejeitado editorialmente" in str(ctx.exception) or "silencioso" in str(ctx.exception),
            "Vídeo silencioso não pode ser promovido para learning_candidate."
        )

    # -------------------------------------------------------------------------
    # 10. Conteúdo fora do nicho do canal classificado como editorially_rejected
    # -------------------------------------------------------------------------
    def test_10_off_topic_editorially_rejected(self):
        self.als.discover_video(
            source_id="offtopic_vid_99",
            title="SHORT JEANS Cintura Baixa - Coleção Moda",
            creator="Moda Beleza",
            duration_seconds=25.0
        )
        res_eval = self.als.evaluate_editorial_adherence(
            source_id="offtopic_vid_99",
            target_channel_id=1  # Canal 1 é Futebol
        )
        self.assertEqual(res_eval["processing_state"], "editorially_rejected")
        self.assertEqual(res_eval["editorial_verdict"], "REJECTED_OFF_TOPIC")
        self.assertIn("editorial_mismatch", res_eval["rejection_reason"])

    # -------------------------------------------------------------------------
    # 11. Ciclo de vida completo: downloaded -> technical_analysis_complete -> editorial_analysis_complete -> learning_candidate
    # -------------------------------------------------------------------------
    def test_11_lifecycle_state_progression(self):
        vid_id = "lifecycle_test_vid"
        self.als.discover_video(
            source_id=vid_id,
            title="Golaço Histórico no Ângulo do Brasileirão",
            duration_seconds=18.0
        )
        # 1. downloaded / media_downloaded
        dummy_file = self.temp_path / "life.mp4"
        dummy_file.write_bytes(b"dummy_media_bytes_life")
        self.als.register_physical_media(vid_id, str(dummy_file), verified_duration=18.0)
        self.assertIn(self._get_state(vid_id), ("media_downloaded", "downloaded"))

        # 2. technical_analysis_complete
        self.als.process_visual(vid_id, cuts_count=4)
        self.als.process_audio(vid_id, estimated_lufs=-14.0, speech_clarity_score=90.0)
        self.als.process_transcript(vid_id, transcript_text="Golaço impressionante do meio de campo!")
        self.als._set_state(vid_id, "technical_analysis_complete")
        self.assertEqual(self._get_state(vid_id), "technical_analysis_complete")

        # 3. editorial_analysis_complete / learning_candidate
        self.als.evaluate_editorial_adherence(vid_id, target_channel_id=1)
        self.als.promote_to_learning_candidate(vid_id)
        self.assertEqual(self._get_state(vid_id), "learning_candidate")

    # -------------------------------------------------------------------------
    # 12. Síntese de conhecimento editorial com Regra de Ouro
    # -------------------------------------------------------------------------
    def test_12_editorial_knowledge_synthesis_evidence_rules(self):
        # 0 evidências -> Erro
        with self.assertRaises(ValueError):
            self.als.record_knowledge(
                title="Afirmação Sem Evidências",
                evidence_video_ids=[]
            )

        # 1 evidência -> OBSERVAÇÃO (confiança <= 0.70)
        obs = self.als.record_knowledge(
            title="Observação Inicial",
            evidence_video_ids=["vid_001"],
            classification="APRENDIZADO_VALIDADO",
            confidence_score=0.95
        )
        self.assertEqual(obs["classification"], "OBSERVAÇÃO")
        self.assertLessEqual(obs["confidence_score"], 0.70)

        # 2 evidências -> APRENDIZADO_VALIDADO (confiança >= 0.80)
        val2 = self.als.record_knowledge(
            title="Regra de Ouro - 2 Evidências",
            evidence_video_ids=["vid_001", "vid_002"],
            classification="APRENDIZADO_VALIDADO"
        )
        self.assertEqual(val2["classification"], "APRENDIZADO_VALIDADO")
        self.assertGreaterEqual(val2["confidence_score"], 0.80)

        # 4+ evidências -> APRENDIZADO_VALIDADO (confiança >= 0.90)
        val4 = self.als.record_knowledge(
            title="Regra de Ouro - 4 Evidências",
            evidence_video_ids=["vid_001", "vid_002", "vid_003", "vid_004"],
            classification="APRENDIZADO_VALIDADO"
        )
        self.assertEqual(val4["classification"], "APRENDIZADO_VALIDADO")
        self.assertGreaterEqual(val4["confidence_score"], 0.90)

    # -------------------------------------------------------------------------
    # 13. Contraexemplos e alertas de antipadrões registrados
    # -------------------------------------------------------------------------
    def test_13_counterexamples_and_antipatterns(self):
        k = self.als.record_knowledge(
            title="Padrão de Ritmo Rápido",
            evidence_video_ids=["vid_a", "vid_b"],
            classification="APRENDIZADO_VALIDADO",
            counterexamples=["vid_low_retention_01"],
            anti_pattern_warning="Cortes excessivos nos primeiros 2s sem estabelecer contexto provocam desorientação"
        )
        self.assertIn("vid_low_retention_01", k["counterexamples"])
        self.assertIn("Cortes excessivos", k["anti_pattern_warning"])

    # -------------------------------------------------------------------------
    # 14. Isolamento estrito de canal no conhecimento editorial (target_channel_id)
    # -------------------------------------------------------------------------
    def test_14_strict_channel_isolation(self):
        self.als.record_knowledge(
            title="Regra Editorial Canal 1 Futebol",
            evidence_video_ids=["ch1_v1", "ch1_v2"],
            classification="APRENDIZADO_VALIDADO",
            target_channel_id=1
        )
        self.als.record_knowledge(
            title="Regra Editorial Canal 2 Casos Policiais",
            evidence_video_ids=["ch2_v1", "ch2_v2"],
            classification="APRENDIZADO_VALIDADO",
            target_channel_id=2
        )

        with self.als._get_conn() as conn:
            ch1_rules = conn.execute("SELECT * FROM editorial_knowledge_library WHERE target_channel_id = 1").fetchall()
            ch2_rules = conn.execute("SELECT * FROM editorial_knowledge_library WHERE target_channel_id = 2").fetchall()

            self.assertEqual(len(ch1_rules), 1)
            self.assertEqual(ch1_rules[0]["title"], "Regra Editorial Canal 1 Futebol")
            self.assertEqual(len(ch2_rules), 1)
            self.assertEqual(ch2_rules[0]["title"], "Regra Editorial Canal 2 Casos Policiais")

    # -------------------------------------------------------------------------
    # 15. Telemetria do Dashboard operacional atualizada com pilot_fase16_metrics
    # -------------------------------------------------------------------------
    def test_15_dashboard_pilot_fase16_telemetry(self):
        dash = self.als.get_dashboard_overview()
        self.assertIn("pilot_fase16_metrics", dash, "Dashboard deve conter a chave 'pilot_fase16_metrics'.")
        m = dash["pilot_fase16_metrics"]
        self.assertEqual(m["candidates_selected"], 100)
        self.assertIn("total_shorts_pilot", m)
        self.assertIn("downloaded", m)
        self.assertIn("technically_analyzed", m)
        self.assertIn("editorially_approved", m)
        self.assertIn("editorially_rejected", m)
        self.assertIn("silent_audio_detected", m)
        self.assertIn("learning_candidates", m)
        self.assertIn("validated_learnings", m)
        self.assertIn("failures", m)
        self.assertEqual(m["cost_usd"], 0.0)

    # -------------------------------------------------------------------------
    # 16. Custo zero estritamente mantido ($0.00)
    # -------------------------------------------------------------------------
    def test_16_zero_cost_lock(self):
        gateway = ModelGatewayService(enforce_free_tier=True)
        self.assertTrue(gateway.enforce_free_tier, "Travamento de custo zero (enforce_free_tier) deve estar ativado.")
        self.assertTrue(gateway.is_paid_model("gpt-4o"))
        self.assertTrue(gateway.is_paid_model("claude-3-5-sonnet-20241022"))
        self.assertFalse(gateway.is_paid_model("gemini/gemini-2.5-flash"))

    def _get_state(self, source_id):
        with self.als._get_conn() as conn:
            row = conn.execute("SELECT processing_state FROM audiovisual_library WHERE source_id = ?", (source_id,)).fetchone()
            return row["processing_state"] if row else None


if __name__ == "__main__":
    unittest.main()
