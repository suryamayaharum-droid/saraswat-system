#!/usr/bin/env python3
"""
Saraswat Agent Orchestrator v1.0
Orquestracao de sub-agentes inspirada no deer-flow.

Permite criar, gerenciar e coordenar sub-agentes especializados
que trabalham em paralelo para resolver tarefas complexas.

Arquitetura:
  - Orchestrator: coordena os sub-agentes
  - SubAgent: agente especializado com tarefa especifica
  - Task: unidade de trabalho
  - Result: resultado de uma tarefa
"""

import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field

MEMORY_DIR = Path("D:/.openclaude/memory")


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRole(Enum):
    PLANNER = "planner"
    EXECUTOR = "executor"
    RESEARCHER = "researcher"
    CODER = "coder"
    ANALYST = "analyst"


@dataclass
class Task:
    id: str
    description: str
    role: AgentRole
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)


@dataclass
class SubAgent:
    name: str
    role: AgentRole
    system_prompt: str
    tasks_completed: int = 0
    is_busy: bool = False


class AgentOrchestrator:
    """
    Orquestrador de agentes especializados.

    Uso:
        orch = AgentOrchestrator()
        orch.create_agent("researcher", AgentRole.RESEARCHER)
        task = orch.submit_task("Pesquisar X", AgentRole.RESEARCHER)
        results = orch.run_cycle()
    """

    def __init__(self):
        self.agents: Dict[str, SubAgent] = {}
        self.tasks: Dict[str, Task] = {}
        self.results: List[Dict[str, Any]] = []
        self._task_counter = 0

    def create_agent(self, name: str, role: AgentRole, system_prompt: str = "") -> SubAgent:
        """Cria um novo sub-agente."""
        if not system_prompt:
            system_prompt = self._default_prompt(role)
        agent = SubAgent(name=name, role=role, system_prompt=system_prompt)
        self.agents[name] = agent
        return agent

    def _default_prompt(self, role: AgentRole) -> str:
        prompts = {
            AgentRole.PLANNER: "Voce e um planejador. Analise tarefas complexas e divida em sub-tarefas menores e ordenadas.",
            AgentRole.EXECUTOR: "Voce e um executor. Execute tarefas de forma eficiente e reporte resultados.",
            AgentRole.RESEARCHER: "Voce e um pesquisador. Busque informacoes, analise dados e sintetize descobertas.",
            AgentRole.CODER: "Voce e um programador. Escreva codigo limpo, testado e documentado.",
            AgentRole.ANALYST: "Voce e um analista. Analise dados, identifique padroes e gere insights.",
        }
        return prompts.get(role, "Voce e um agente especializado.")

    def submit_task(self, description: str, role: AgentRole, dependencies: List[str] = None) -> Task:
        """Submete uma nova tarefa."""
        self._task_counter += 1
        task = Task(
            id=f"task_{self._task_counter}",
            description=description,
            role=role,
            dependencies=dependencies or [],
        )
        self.tasks[task.id] = task
        return task

    def get_pending_tasks(self) -> List[Task]:
        """Retorna tarefas pendentes cujas dependencias foram completadas."""
        pending = []
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            # Check dependencies
            deps_met = all(
                self.tasks.get(dep_id, Task(id="", description="", role=AgentRole.EXECUTOR)).status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
            )
            if deps_met:
                pending.append(task)
        return pending

    def assign_task(self, task: Task, agent_name: str) -> bool:
        """Atribui uma tarefa a um agente."""
        agent = self.agents.get(agent_name)
        if not agent or agent.is_busy:
            return False
        if agent.role != task.role:
            return False

        agent.is_busy = True
        task.status = TaskStatus.RUNNING
        return True

    def complete_task(self, task_id: str, result: str):
        """Marca uma tarefa como completada."""
        task = self.tasks.get(task_id)
        if not task:
            return
        task.status = TaskStatus.COMPLETED
        task.result = result
        task.completed_at = datetime.now().isoformat()
        self.results.append({
            "task_id": task_id,
            "description": task.description,
            "result": result,
            "completed_at": task.completed_at,
        })

    def fail_task(self, task_id: str, error: str):
        """Marca uma tarefa como falha."""
        task = self.tasks.get(task_id)
        if not task:
            return
        task.status = TaskStatus.FAILED
        task.error = error
        task.completed_at = datetime.now().isoformat()

    def get_status(self) -> Dict[str, Any]:
        """Retorna status do orquestrador."""
        tasks_by_status = {}
        for task in self.tasks.values():
            status = task.status.value
            tasks_by_status[status] = tasks_by_status.get(status, 0) + 1

        return {
            "agents": len(self.agents),
            "tasks": len(self.tasks),
            "tasks_by_status": tasks_by_status,
            "results": len(self.results),
            "agents_detail": {
                name: {
                    "role": agent.role.value,
                    "busy": agent.is_busy,
                    "completed": agent.tasks_completed,
                }
                for name, agent in self.agents.items()
            },
        }

    def run_parallel(self, tasks: List[Task]) -> List[Dict[str, Any]]:
        """
        Executa tarefas em paralelo (simulado).
        Na pratica, cada tarefa seria um subprocesso ou chamada de API.
        """
        results = []
        for task in tasks:
            task.status = TaskStatus.RUNNING
            # Simulacao - na pratica, executaria o agente real
            result = f"[{task.role.value}] Processado: {task.description[:50]}"
            self.complete_task(task.id, result)
            results.append({"task_id": task.id, "result": result})
        return results


# Singleton
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator


if __name__ == "__main__":
    orch = get_orchestrator()

    # Create agents
    orch.create_agent("planner_1", AgentRole.PLANNER)
    orch.create_agent("executor_1", AgentRole.EXECUTOR)
    orch.create_agent("researcher_1", AgentRole.RESEARCHER)

    # Submit tasks
    orch.submit_task("Analisar estado do sistema", AgentRole.ANALYST)
    orch.submit_task("Buscar atualizacoes nos repositorios", AgentRole.RESEARCHER)
    orch.submit_task("Limpar arquivos temporarios", AgentRole.EXECUTOR)

    # Run
    pending = orch.get_pending_tasks()
    print(f"Pending tasks: {len(pending)}")
    results = orch.run_parallel(pending)

    print(json.dumps(orch.get_status(), indent=2, ensure_ascii=False))
