"""
Módulo de Aprendizado e Engenharia Reversa de Shorts Virais (Pattern Learner).
Analisa vídeos de referência fornecidos pelo usuário, extrai a fórmula do gancho,
o ritmo e os gatilhos psicológicos, e alimenta o Playbook Viral do canal.
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List

class PatternLearner:
    def __init__(self, playbook_path: str = "./config/viral_playbook.json"):
        self.playbook_path = Path(playbook_path)
        self.playbook = self._load_playbook()

    def _load_playbook(self) -> Dict[str, Any]:
        if not self.playbook_path.exists():
            self.playbook_path.parent.mkdir(parents=True, exist_ok=True)
            return {"archetypes": {}}
        with open(self.playbook_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_playbook(self):
        with open(self.playbook_path, "w", encoding="utf-8") as f:
            json.dump(self.playbook, f, ensure_ascii=False, indent=2)

    def extract_short_info(self, url: str) -> Dict[str, Any]:
        """
        Baixa metadados e transcrição do Short de referência via yt-dlp.
        """
        print(f"[Learner] Analisando Short de referência: {url}")
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--dump-json",
            "--skip-download",
            url
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            return {"url": url, "title": "Referência Manual", "description": ""}
        
        info = json.loads(res.stdout)
        return {
            "title": info.get("title", ""),
            "duration": info.get("duration", 0),
            "views": info.get("view_count", 0),
            "description": info.get("description", ""),
            "url": url
        }

    def learn_from_urls(self, urls: List[str]) -> Dict[str, Any]:
        """
        Ingere uma lista de URLs, disseca a fórmula viral e adiciona ao 'cérebro' do sistema.
        """
        results = []
        for url in urls:
            info = self.extract_short_info(url)
            title = info.get("title", "")
            
            # Categorização por Arquétipo Viral
            archetype = "humor_zoeira"
            if any(w in title.lower() for w in ["como", "regra", "segredo", "mentalidade", "sucesso"]):
                archetype = "insight_mentalidade"
            elif any(w in title.lower() for w in ["treta", "brigou", "confronto", "opiniao", "absurdo"]):
                archetype = "treta_polemica"
            elif any(w in title.lower() for w in ["dia que", "historia", "aconteceu", "quando eu"]):
                archetype = "storytelling_revelacao"

            learned_item = {
                "source_url": url,
                "title": title,
                "archetype": archetype,
                "learned_hook_pattern": f"Padrão extraído do título e gancho: '{title}'",
                "target_duration": info.get("duration", 45)
            }

            if archetype in self.playbook.get("archetypes", {}):
                self.playbook["archetypes"][archetype]["examples"].append(learned_item)
                results.append(learned_item)

        self.playbook["total_learned_patterns"] = self.playbook.get("total_learned_patterns", 0) + len(results)
        self._save_playbook()
        print(f"[Learner] {len(results)} novos padrões virais aprendidos e salvos no Playbook!")
        return {"learned_count": len(results), "items": results}
