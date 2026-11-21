"""
Base Agent Interface para a Multi-Skill AI Content Company.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from memory.central_memory import CentralMemory

class AgentEvaluationResult(BaseModel):
    agent_name: str
    specialty: str
    score: int = Field(..., ge=0, le=100, description="Nota de 0 a 100")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiança na avaliação")
    recommendation: str
    detailed_metrics: Dict[str, Any] = Field(default_factory=dict)
    flags: List[str] = Field(default_factory=list)
    suggested_improvements: List[str] = Field(default_factory=list)

class BaseSpecialistAgent(ABC):
    def __init__(self, name: str, role: str, specialty: str, memory: Optional[CentralMemory] = None):
        self.name = name
        self.role = role
        self.specialty = specialty
        self.memory = memory or CentralMemory()
        self.working_memory: Dict[str, Any] = {}
        self.evaluation_criteria: List[str] = []

    def set_working_memory(self, key: str, value: Any):
        self.working_memory[key] = value

    def get_working_memory(self, key: str, default: Any = None) -> Any:
        return self.working_memory.get(key, default)

    def clear_working_memory(self):
        self.working_memory.clear()

    @abstractmethod
    def evaluate(self, input_data: Dict[str, Any]) -> AgentEvaluationResult:
        """Executa a análise especializada sobre o conteúdo recebido."""
        pass

    def log_decision(self, target_type: str, target_id: Optional[int],
                     input_data: Dict[str, Any], result: AgentEvaluationResult) -> int:
        """Registra a deliberação na memória central do sistema."""
        return self.memory.log_agent_decision(
            agent_name=self.name,
            target_type=target_type,
            target_id=target_id,
            input_data=input_data,
            analysis=result.model_dump(),
            score=result.score,
            confidence=result.confidence,
            recommendation=result.recommendation
        )
