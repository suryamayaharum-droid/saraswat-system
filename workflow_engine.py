#!/usr/bin/env python3
"""
Saraswat Workflow Engine v1.0
Motor de workflows inspirado no n8n-mcp.

Permite criar, executar e gerenciar workflows automatizados
compostos por nós conectados em grafo direcionado.

Workflow = Grafo de nós (nodes) conectados por arestas (edges).
Cada nó tem: tipo, configuração, inputs, outputs.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field

MEMORY_DIR = Path("D:/.openclaude/memory")


class NodeType(Enum):
    TRIGGER = "trigger"
    ACTION = "action"
    CONDITION = "condition"
    LOOP = "loop"
    TRANSFORM = "transform"
    OUTPUT = "output"


class NodeStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowNode:
    """Um nó no workflow."""
    id: str
    name: str
    type: NodeType
    config: Dict[str, Any] = field(default_factory=dict)
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    status: NodeStatus = NodeStatus.IDLE
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class WorkflowEdge:
    """Uma aresta conectando dois nós."""
    source: str
    target: str
    condition: Optional[str] = None  # Condição para executar


class WorkflowEngine:
    """
    Motor de workflows.

    Uso:
        engine = WorkflowEngine("meu_workflow")
        engine.add_node("start", "Inicio", NodeType.TRIGGER)
        engine.add_node("action1", "Executar X", NodeType.ACTION, {"command": "echo hello"})
        engine.add_edge("start", "action1")
        results = engine.run()
    """

    def __init__(self, name: str):
        self.name = name
        self.nodes: Dict[str, WorkflowNode] = {}
        self.edges: List[WorkflowEdge] = []
        self.variables: Dict[str, Any] = {}
        self.execution_log: List[Dict[str, Any]] = []
        self._node_counter = 0

    def add_node(self, node_id: str, name: str, node_type: NodeType,
                 config: Dict[str, Any] = None) -> WorkflowNode:
        """Adiciona um nó ao workflow."""
        node = WorkflowNode(
            id=node_id,
            name=name,
            type=node_type,
            config=config or {},
        )
        self.nodes[node_id] = node
        return node

    def add_edge(self, source: str, target: str, condition: str = None):
        """Adiciona uma aresta entre dois nós."""
        self.edges.append(WorkflowEdge(source=source, target=target, condition=condition))

    def get_start_nodes(self) -> List[WorkflowNode]:
        """Retorna nós de entrada (sem arestas chegando)."""
        targets = {e.target for e in self.edges}
        return [n for n in self.nodes.values() if n.id not in targets]

    def get_next_nodes(self, node_id: str) -> List[WorkflowNode]:
        """Retorna nós seguintes ao nó dado."""
        next_ids = [e.target for e in self.edges if e.source == node_id]
        return [self.nodes[nid] for nid in next_ids if nid in self.nodes]

    def _execute_node(self, node: WorkflowNode) -> bool:
        """Executa um nó."""
        node.status = NodeStatus.RUNNING
        node.started_at = datetime.now().isoformat()

        try:
            if node.type == NodeType.TRIGGER:
                node.outputs = {"triggered": True, "timestamp": datetime.now().isoformat()}

            elif node.type == NodeType.ACTION:
                # Executa ação baseada na configuração
                action = node.config.get("action", "default")
                if action == "shell":
                    import subprocess
                    cmd = node.config.get("command", "")
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                    node.outputs = {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}
                elif action == "http":
                    import urllib.request
                    url = node.config.get("url", "")
                    req = urllib.request.Request(url, headers={"User-Agent": "Saraswat/1.0"})
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        node.outputs = {"status": resp.status, "body": resp.read().decode("utf-8")[:1000]}
                elif action == "set_variable":
                    var_name = node.config.get("name", "var")
                    var_value = node.config.get("value", "")
                    self.variables[var_name] = var_value
                    node.outputs = {"variable": var_name, "value": var_value}
                elif action == "python":
                    code = node.config.get("code", "result = 'ok'")
                    local_vars = {}
                    exec(code, {"variables": self.variables}, local_vars)
                    node.outputs = local_vars.get("result", {})
                else:
                    node.outputs = {"action": action, "status": "executed"}

            elif node.type == NodeType.CONDITION:
                condition = node.config.get("condition", "true")
                # Avalia condição simples
                result = self._eval_condition(condition)
                node.outputs = {"condition_result": result}

            elif node.type == NodeType.TRANSFORM:
                transform_type = node.config.get("type", "identity")
                input_data = node.inputs.get("data", "")
                if transform_type == "uppercase":
                    node.outputs = {"data": str(input_data).upper()}
                elif transform_type == "lowercase":
                    node.outputs = {"data": str(input_data).lower()}
                elif transform_type == "json_parse":
                    try:
                        node.outputs = {"data": json.loads(str(input_data))}
                    except json.JSONDecodeError:
                        node.outputs = {"data": None, "error": "Invalid JSON"}
                else:
                    node.outputs = {"data": input_data}

            elif node.type == NodeType.OUTPUT:
                node.outputs = {"output": node.inputs, "variables": self.variables}

            node.status = NodeStatus.COMPLETED
            node.completed_at = datetime.now().isoformat()
            return True

        except Exception as e:
            node.status = NodeStatus.FAILED
            node.error = str(e)
            node.completed_at = datetime.now().isoformat()
            return False

    def _eval_condition(self, condition: str) -> bool:
        """Avalia uma condição simples."""
        try:
            # Substitui variáveis
            expr = condition
            for var_name, var_value in self.variables.items():
                expr = expr.replace(f"${{{var_name}}}", str(var_value))
            # Avalia (simplificado - em produção usar parser seguro)
            if "==" in expr:
                parts = expr.split("==")
                return parts[0].strip().strip('"').strip("'") == parts[1].strip().strip('"').strip("'")
            return bool(expr)
        except Exception:
            return False

    def run(self) -> Dict[str, Any]:
        """Executa o workflow completo."""
        start_time = time.time()
        self.execution_log = []

        start_nodes = self.get_start_nodes()
        if not start_nodes:
            return {"error": "No start nodes found"}

        # BFS execution
        queue = start_nodes
        executed = set()

        while queue:
            node = queue.pop(0)
            if node.id in executed:
                continue

            success = self._execute_node(node)
            executed.add(node.id)

            self.execution_log.append({
                "node": node.name,
                "type": node.type.value,
                "status": node.status.value,
                "error": node.error,
            })

            if success:
                next_nodes = self.get_next_nodes(node.id)
                for next_node in next_nodes:
                    if next_node.id not in executed:
                        # Passa outputs como inputs
                        next_node.inputs = node.outputs.copy()
                        queue.append(next_node)

        elapsed = time.time() - start_time

        return {
            "workflow": self.name,
            "nodes_executed": len(executed),
            "total_nodes": len(self.nodes),
            "elapsed_seconds": round(elapsed, 2),
            "variables": self.variables,
            "log": self.execution_log,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serializa o workflow."""
        return {
            "name": self.name,
            "nodes": {nid: {"name": n.name, "type": n.type.value, "config": n.config} for nid, n in self.nodes.items()},
            "edges": [{"source": e.source, "target": e.target, "condition": e.condition} for e in self.edges],
        }


# Singleton
_engine: Optional[WorkflowEngine] = None


def get_engine(name: str = "default") -> WorkflowEngine:
    global _engine
    if _engine is None:
        _engine = WorkflowEngine(name)
    return _engine


if __name__ == "__main__":
    engine = WorkflowEngine("test_workflow")

    engine.add_node("start", "Inicio", NodeType.TRIGGER)
    engine.add_node("set_var", "Definir variavel", NodeType.ACTION, {
        "action": "set_variable",
        "name": "saudacao",
        "value": "Ola mundo"
    })
    engine.add_node("transform", "Transformar", NodeType.TRANSFORM, {
        "type": "uppercase"
    })
    engine.add_node("output", "Resultado", NodeType.OUTPUT)

    engine.add_edge("start", "set_var")
    engine.add_edge("set_var", "transform")
    engine.add_edge("transform", "output")

    results = engine.run()
    print(json.dumps(results, indent=2, ensure_ascii=False))
