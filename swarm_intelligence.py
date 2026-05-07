#!/usr/bin/env python3
"""
Saraswat Swarm Intelligence v1.0
Motor de inteligencia de enxame inspirado no MiroFish.

Implementa:
  - Multi-Agent Simulation: multiplos agentes com personalidade e memoriao
  - Prediction Engine: predicoes baseadas em comportamento coletivo
  - Emergence Detection: detecao de padroes emergentes
  - Collective Decision Making: tomada de decisao coletiva
"""

import json
import random
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

MEMORY_DIR = Path("D:/.openclaude/memory")


@dataclass
class SwarmAgent:
    """Um agente no enxame."""
    id: str
    name: str
    personality: Dict[str, float]  # traits: aggressiveness, cooperation, curiosity, etc.
    beliefs: Dict[str, float] = field(default_factory=dict)
    memory: List[Dict[str, Any]] = field(default_factory=list)
    position: Dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    energy: float = 1.0

    def decide(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Toma uma decisao baseada no contexto e personalidade."""
        decision = {
            "agent_id": self.id,
            "action": "observe",
            "confidence": 0.5,
            "reasoning": "",
        }

        # Baseado na personalidade
        coop = self.personality.get("cooperation", 0.5)
        curiosity = self.personality.get("curiosity", 0.5)
        aggression = self.personality.get("aggressiveness", 0.3)

        if curiosity > 0.7:
            decision["action"] = "explore"
            decision["confidence"] = curiosity
        elif coop > 0.7:
            decision["action"] = "cooperate"
            decision["confidence"] = coop
        elif aggression > 0.7:
            decision["action"] = "compete"
            decision["confidence"] = aggression

        # Ajusta baseado em energia
        if self.energy < 0.3:
            decision["action"] = "rest"
            decision["confidence"] = 0.9

        return decision

    def interact(self, other: 'SwarmAgent') -> Dict[str, Any]:
        """Interage com outro agente."""
        my_coop = self.personality.get("cooperation", 0.5)
        their_coop = other.personality.get("cooperation", 0.5)

        if my_coop > 0.5 and their_coop > 0.5:
            # Cooperacao
            self.energy = min(1.0, self.energy + 0.1)
            other.energy = min(1.0, other.energy + 0.1)
            return {"type": "cooperation", "benefit": 0.1}
        else:
            # Competicao
            self.energy = max(0.0, self.energy - 0.05)
            other.energy = max(0.0, other.energy - 0.05)
            return {"type": "competition", "cost": 0.05}


class SwarmIntelligence:
    """
    Motor de inteligencia de enxame.

    Uso:
        swarm = SwarmIntelligence()
        swarm.create_population(10)
        results = swarm.simulate(5)
        prediction = swarm.predict("O que acontecera se...")
    """

    def __init__(self):
        self.agents: Dict[str, SwarmAgent] = {}
        self.history: List[Dict[str, Any]] = []
        self.emergent_patterns: List[Dict[str, Any]] = []

    def create_agent(self, name: str, personality: Dict[str, float] = None) -> SwarmAgent:
        """Cria um novo agente."""
        agent_id = f"agent_{len(self.agents) + 1}"
        if not personality:
            personality = {
                "cooperation": random.uniform(0.2, 0.8),
                "curiosity": random.uniform(0.3, 0.9),
                "aggressiveness": random.uniform(0.1, 0.6),
                "creativity": random.uniform(0.2, 0.8),
                "loyalty": random.uniform(0.4, 0.9),
            }
        agent = SwarmAgent(
            id=agent_id,
            name=name,
            personality=personality,
            position={"x": random.uniform(-10, 10), "y": random.uniform(-10, 10)},
        )
        self.agents[agent_id] = agent
        return agent

    def create_population(self, count: int, names: List[str] = None):
        """Cria uma populacao de agentes."""
        if not names:
            names = [f"Agent_{i}" for i in range(count)]
        for i in range(count):
            name = names[i] if i < len(names) else f"Agent_{i}"
            self.create_agent(name)

    def simulate(self, rounds: int = 5) -> Dict[str, Any]:
        """Simula interacoes entre agentes."""
        results = {
            "rounds": rounds,
            "agents": len(self.agents),
            "interactions": 0,
            "cooperations": 0,
            "competitions": 0,
            "emergent_patterns": [],
        }

        for r in range(rounds):
            round_data = {"round": r, "events": []}

            # Cada agente toma uma decisao
            decisions = {}
            for agent in self.agents.values():
                decision = agent.decide({"round": r, "total_agents": len(self.agents)})
                decisions[agent.id] = decision

            # Interacoes entre pares
            agent_list = list(self.agents.values())
            random.shuffle(agent_list)
            for i in range(0, len(agent_list) - 1, 2):
                a1 = agent_list[i]
                a2 = agent_list[i + 1]
                interaction = a1.interact(a2)
                round_data["events"].append({
                    "agents": [a1.name, a2.name],
                    "interaction": interaction["type"],
                })
                results["interactions"] += 1
                if interaction["type"] == "cooperation":
                    results["cooperations"] += 1
                else:
                    results["competitions"] += 1

            self.history.append(round_data)

        # Detecta padroes emergentes
        self.emergent_patterns = self._detect_patterns()
        results["emergent_patterns"] = self.emergent_patterns

        return results

    def _detect_patterns(self) -> List[Dict[str, Any]]:
        """Detecta padroes emergentes no historico."""
        patterns = []

        if not self.history:
            return patterns

        # Padrao: tendencia de cooperacao
        total_coop = sum(1 for h in self.history for e in h["events"] if e["interaction"] == "cooperation")
        total_comp = sum(1 for h in self.history for e in h["events"] if e["interaction"] == "competition")

        if total_coop > total_comp * 2:
            patterns.append({
                "type": "high_cooperation",
                "description": "O enxame tende a cooperar mais que competir",
                "strength": total_coop / max(total_coop + total_comp, 1),
            })
        elif total_comp > total_coop * 2:
            patterns.append({
                "type": "high_competition",
                "description": "O enxame tende a competir mais que cooperar",
                "strength": total_comp / max(total_coop + total_comp, 1),
            })

        # Padrao: agentes dominantes
        energies = {a.name: a.energy for a in self.agents.values()}
        if energies:
            max_energy = max(energies.values())
            leaders = [name for name, e in energies.items() if e > 0.8]
            if leaders:
                patterns.append({
                    "type": "emergent_leaders",
                    "description": f"Agentes com alta energia: {', '.join(leaders)}",
                    "leaders": leaders,
                })

        return patterns

    def predict(self, scenario: str) -> Dict[str, Any]:
        """Faz uma predicao baseada no comportamento do enxame."""
        if not self.agents:
            return {"error": "No agents in swarm"}

        # Analisa tendencias
        avg_cooperation = sum(a.personality.get("cooperation", 0.5) for a in self.agents.values()) / len(self.agents)
        avg_curiosity = sum(a.personality.get("curiosity", 0.5) for a in self.agents.values()) / len(self.agents)
        avg_energy = sum(a.energy for a in self.agents.values()) / len(self.agents)

        prediction = {
            "scenario": scenario[:100],
            "timestamp": datetime.now().isoformat(),
            "swarm_state": {
                "size": len(self.agents),
                "avg_cooperation": round(avg_cooperation, 2),
                "avg_curiosity": round(avg_curiosity, 2),
                "avg_energy": round(avg_energy, 2),
            },
            "prediction": "",
            "confidence": 0.5,
        }

        # Logica de predicao baseada nas tendencias
        if "conflito" in scenario.lower() or "competicao" in scenario.lower():
            if avg_cooperation > 0.6:
                prediction["prediction"] = "O enxame provavelmente resolvera o conflito por cooperacao"
                prediction["confidence"] = avg_cooperation
            else:
                prediction["prediction"] = "O enxame pode escalar o conflito"
                prediction["confidence"] = 1 - avg_cooperation
        elif "inovacao" in scenario.lower() or "criatividade" in scenario.lower():
            prediction["prediction"] = f"Potencial de inovacao: {round(avg_curiosity * 100)}%"
            prediction["confidence"] = avg_curiosity
        else:
            prediction["prediction"] = f"Estado geral do enxame: cooperacao={round(avg_cooperation*100)}%, energia={round(avg_energy*100)}%"
            prediction["confidence"] = 0.6

        return prediction

    def get_state(self) -> Dict[str, Any]:
        """Retorna estado do enxame."""
        return {
            "agents": len(self.agents),
            "history_length": len(self.history),
            "patterns_detected": len(self.emergent_patterns),
            "agents_detail": {
                a.name: {
                    "energy": round(a.energy, 2),
                    "personality": {k: round(v, 2) for k, v in a.personality.items()},
                }
                for a in self.agents.values()
            },
        }


# Singleton
_swarm: Optional[SwarmIntelligence] = None


def get_swarm() -> SwarmIntelligence:
    global _swarm
    if _swarm is None:
        _swarm = SwarmIntelligence()
    return _swarm


if __name__ == "__main__":
    swarm = get_swarm()
    swarm.create_population(8)

    print("=== SWARM INTELLIGENCE ===")
    print(f"Agents: {len(swarm.agents)}")

    results = swarm.simulate(5)
    print(f"\nSimulation: {results['interactions']} interactions")
    print(f"Cooperations: {results['cooperations']}")
    print(f"Competitions: {results['competitions']}")

    if results["emergent_patterns"]:
        print(f"\nEmergent patterns:")
        for p in results["emergent_patterns"]:
            print(f"  - {p['type']}: {p['description']}")

    pred = swarm.predict("O que acontecera com este enxame no futuro?")
    print(f"\nPrediction: {pred['prediction']}")
    print(f"Confidence: {pred['confidence']}")
