"""
Content Company: Mesa Redonda e Coordenação dos 10 Agentes Especializados.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from memory.central_memory import CentralMemory
from agents.specialists import (
    SportsAgent, PodcastAgent, ComedyAgent, StorytellingAgent,
    RetentionAgent, EditingAgent, AudienceAgent, TrendsAgent,
    OriginalityAgent, ContentDirectorAgent
)
from agents.base_agent import AgentEvaluationResult

class ContentCompany:
    def __init__(self, memory: Optional[CentralMemory] = None):
        self.memory = memory or CentralMemory()
        
        # Inicializa a empresa com os 10 especialistas
        self.sports_agent = SportsAgent(memory=self.memory)
        self.podcast_agent = PodcastAgent(memory=self.memory)
        self.comedy_agent = ComedyAgent(memory=self.memory)
        self.storytelling_agent = StorytellingAgent(memory=self.memory)
        self.retention_agent = RetentionAgent(memory=self.memory)
        self.editing_agent = EditingAgent(memory=self.memory)
        self.audience_agent = AudienceAgent(memory=self.memory)
        self.trends_agent = TrendsAgent(memory=self.memory)
        self.originality_agent = OriginalityAgent(memory=self.memory)
        self.director_agent = ContentDirectorAgent(memory=self.memory)

        self.specialists = [
            self.sports_agent,
            self.podcast_agent,
            self.comedy_agent,
            self.storytelling_agent,
            self.retention_agent,
            self.editing_agent,
            self.audience_agent,
            self.trends_agent,
            self.originality_agent
        ]

    def evaluate_candidate_cut(self, candidate_cut: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa a Mesa Redonda:
        Cada um dos 9 especialistas analisa o trecho de forma independente e registra suas métricas.
        O Diretor de Conteúdo recebe todas as avaliações e profere a decisão final.
        """
        evaluations: List[AgentEvaluationResult] = []

        for specialist in self.specialists:
            eval_res = specialist.evaluate(candidate_cut)
            evaluations.append(eval_res)
            
            # Registra no log de decisões da memória central
            specialist.log_decision(
                target_type="candidate_cut",
                target_id=candidate_cut.get("id"),
                input_data={"title": candidate_cut.get("title", ""), "duration": candidate_cut.get("duration")},
                result=eval_res
            )

        # O Diretor de Conteúdo delibera com base nas opiniões dos especialistas
        decision = self.director_agent.deliberate(candidate_cut, evaluations)

        # Registra a decisão final do Diretor
        self.memory.log_agent_decision(
            agent_name=self.director_agent.name,
            target_type="candidate_cut",
            target_id=candidate_cut.get("id"),
            input_data={"candidate_title": candidate_cut.get("title", "")},
            analysis=decision,
            score=decision["final_score"],
            confidence=decision["confidence"],
            recommendation=decision["recommendation"]
        )

        return {
            "candidate_id": candidate_cut.get("id"),
            "title": candidate_cut.get("title", ""),
            "duration": candidate_cut.get("duration", 0),
            "director_verdict": decision,
            "specialist_evaluations": [e.model_dump() for e in evaluations]
        }

    def get_company_roster(self) -> List[Dict[str, Any]]:
        """Retorna a ficha técnica dos 10 agentes da empresa para exibição no Dashboard."""
        all_agents = self.specialists + [self.director_agent]
        return [
            {
                "name": agent.name,
                "role": agent.role,
                "specialty": agent.specialty,
                "criteria": agent.evaluation_criteria
            }
            for agent in all_agents
        ]
