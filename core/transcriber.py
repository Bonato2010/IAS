"""
Módulo de Transcrição e Diarização de Falantes com Timestamps Finais.
Pode usar Faster-Whisper localmente ou a API do Gemini.
"""
import json
from pathlib import Path
from typing import List, Dict, Any

class AudioTranscriber:
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size

    def transcribe_local_whisper(self, audio_path: Path) -> List[Dict[str, Any]]:
        """
        Transcreve o áudio gerando timestamps precisos no nível de palavra (word-level).
        """
        print(f"[Transcriber] Carregando modelo Faster-Whisper ({self.model_size})...")
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise ImportError("faster-whisper não instalado. Execute: pip install faster-whisper")

        model = WhisperModel(self.model_size, device="auto", compute_type="auto")
        segments, info = model.transcribe(
            str(audio_path),
            word_timestamps=True,
            language="pt"
        )

        words_data = []
        for segment in segments:
            for word in segment.words:
                words_data.append({
                    "word": word.word.strip(),
                    "start": round(word.start, 2),
                    "end": round(word.end, 2),
                    "probability": round(word.probability, 2)
                })

        # Salvar cache da transcrição
        json_path = audio_path.with_suffix(".transcript.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(words_data, f, ensure_ascii=False, indent=2)

        print(f"[Transcriber] Transcrição concluída: {len(words_data)} palavras mapeadas.")
        return words_data

    @staticmethod
    def words_to_full_text(words: List[Dict[str, Any]]) -> str:
        """Agrupa palavras em blocos de texto legíveis com indicação temporal."""
        lines = []
        current_chunk = []
        chunk_start = 0.0

        for idx, w in enumerate(words):
            if not current_chunk:
                chunk_start = w["start"]
            current_chunk.append(w["word"])

            # A cada 15 palavras ou no final, fecha uma linha com timestamp
            if len(current_chunk) >= 15 or idx == len(words) - 1:
                lines.append(f"[{chunk_start:.1f}s - {w['end']:.1f}s]: {' '.join(current_chunk)}")
                current_chunk = []

        return "\n".join(lines)
