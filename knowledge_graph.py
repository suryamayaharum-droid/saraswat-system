#!/usr/bin/env python3
"""
Saraswat Knowledge Graph v1.0
Grafo de conhecimento para conectar conceitos, tecnologias e recursos.

Implementa:
  - Nós: conceitos, tecnologias, projetos, skills
  - Arestas: relacionamentos (usa, depende, extende, similar)
  - Busca: caminho entre nós, vizinhos, relevância
  - Indexação: conecta com MemPalace/Obsidian
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque

MEMORY_DIR = Path("D:/.openclaude/memory")
GRAPH_FILE = MEMORY_DIR / "knowledge_graph.json"


class KnowledgeNode:
    """Um nó no grafo de conhecimento."""

    def __init__(self, id: str, label: str, node_type: str,
                 properties: Dict[str, Any] = None):
        self.id = id
        self.label = label
        self.node_type = node_type
        self.properties = properties or {}
        self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "type": self.node_type,
            "properties": self.properties,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeNode":
        node = cls(data["id"], data["label"], data["type"], data.get("properties"))
        node.created_at = data.get("created_at", datetime.now().isoformat())
        return node


class KnowledgeEdge:
    """Uma aresta no grafo de conhecimento."""

    def __init__(self, source: str, target: str, relation: str,
                 weight: float = 1.0, properties: Dict[str, Any] = None):
        self.source = source
        self.target = target
        self.relation = relation
        self.weight = weight
        self.properties = properties or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "weight": self.weight,
            "properties": self.properties,
        }


class KnowledgeGraph:
    """
    Grafo de conhecimento do sistema Saraswat.

    Uso:
        kg = KnowledgeGraph()
        kg.add_node("python", "Python", "language")
        kg.add_node("ollama", "Ollama", "tool")
        kg.add_edge("saraswat", "python", "uses")
        kg.add_edge("saraswat", "ollama", "integrates")
        paths = kg.find_path("python", "ollama")
        relevant = kg.search("LLM")
    """

    def __init__(self):
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: List[KnowledgeEdge] = []
        self._adjacency: Dict[str, List[Tuple[str, str, float]]] = defaultdict(list)  # node -> [(target, relation, weight)]
        self._reverse_adj: Dict[str, List[Tuple[str, str, float]]] = defaultdict(list)

    def add_node(self, node_id: str, label: str, node_type: str,
                 properties: Dict[str, Any] = None) -> KnowledgeNode:
        """Adiciona um nó ao grafo."""
        node = KnowledgeNode(node_id, label, node_type, properties)
        self.nodes[node_id] = node
        return node

    def add_edge(self, source: str, target: str, relation: str,
                 weight: float = 1.0, properties: Dict[str, Any] = None):
        """Adiciona uma aresta ao grafo."""
        if source not in self.nodes or target not in self.nodes:
            raise ValueError(f"Nodes must exist: {source} -> {target}")

        edge = KnowledgeEdge(source, target, relation, weight, properties)
        self.edges.append(edge)
        self._adjacency[source].append((target, relation, weight))
        self._reverse_adj[target].append((source, relation, weight))

    def get_neighbors(self, node_id: str, direction: str = "outgoing") -> List[Dict[str, Any]]:
        """Retorna vizinhos de um nó."""
        if direction == "outgoing":
            neighbors = self._adjacency.get(node_id, [])
        else:
            neighbors = self._reverse_adj.get(node_id, [])

        result = []
        for target_id, relation, weight in neighbors:
            if target_id in self.nodes:
                result.append({
                    "node": self.nodes[target_id].to_dict(),
                    "relation": relation,
                    "weight": weight,
                })
        return result

    def find_path(self, source: str, target: str, max_depth: int = 6) -> List[Dict[str, Any]]:
        """Encontra caminho entre dois nós (BFS)."""
        if source not in self.nodes or target not in self.nodes:
            return []

        visited = {source}
        queue = deque([(source, [])])

        while queue:
            current, path = queue.popleft()

            if len(path) >= max_depth:
                continue

            for next_node, relation, weight in self._adjacency.get(current, []):
                if next_node == target:
                    return path + [{"from": current, "to": next_node, "relation": relation}]

                if next_node not in visited:
                    visited.add(next_node)
                    queue.append((next_node, path + [{"from": current, "to": next_node, "relation": relation}]))

        return []

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Busca nós por texto."""
        query_lower = query.lower().strip()
        results = []

        for node in self.nodes.values():
            score = 0
            if query_lower in node.label.lower():
                score += 10
            if query_lower in node.node_type.lower():
                score += 5
            if query_lower in node.id.lower():
                score += 8
            for val in node.properties.values():
                if isinstance(val, str) and query_lower in val.lower():
                    score += 3

            if score > 0:
                results.append({
                    "node": node.to_dict(),
                    "score": score,
                    "neighbors": len(self._adjacency.get(node.id, [])),
                })

        return sorted(results, key=lambda x: x["score"], reverse=True)

    def get_central_nodes(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Retorna nós mais conectados (centralidade de grau)."""
        centrality = {}
        for node_id in self.nodes:
            out_degree = len(self._adjacency.get(node_id, []))
            in_degree = len(self._reverse_adj.get(node_id, []))
            centrality[node_id] = out_degree + in_degree

        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        return [
            {
                "node": self.nodes[nid].to_dict(),
                "connections": count,
            }
            for nid, count in sorted_nodes[:top_n]
        ]

    def get_communities(self) -> Dict[str, List[str]]:
        """Detecta comunidades simples (componentes fracamente conectados)."""
        visited = set()
        communities = {}

        for node_id in self.nodes:
            if node_id in visited:
                continue

            community = []
            queue = deque([node_id])

            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)
                community.append(current)

                for target, _, _ in self._adjacency.get(current, []):
                    if target not in visited:
                        queue.append(target)
                for source, _, _ in self._reverse_adj.get(current, []):
                    if source not in visited:
                        queue.append(source)

            if community:
                communities[f"community_{len(communities) + 1}"] = community

        return communities

    def save(self):
        """Salva o grafo em arquivo JSON."""
        data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
        }
        GRAPH_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def load(self):
        """Carrega o grafo de arquivo JSON."""
        if GRAPH_FILE.exists():
            data = json.loads(GRAPH_FILE.read_text(encoding="utf-8"))
            for nid, n_data in data.get("nodes", {}).items():
                self.nodes[nid] = KnowledgeNode.from_dict(n_data)
            for e_data in data.get("edges", []):
                self.add_edge(e_data["source"], e_data["target"], e_data["relation"], e_data.get("weight", 1.0))

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do grafo."""
        types = defaultdict(int)
        relations = defaultdict(int)
        for node in self.nodes.values():
            types[node.node_type] += 1
        for edge in self.edges:
            relations[edge.relation] += 1

        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "node_types": dict(types),
            "relation_types": dict(relations),
            "communities": len(self.get_communities()),
        }


def build_saraswat_graph() -> KnowledgeGraph:
    """Constrói o grafo de conhecimento inicial do Saraswat."""
    kg = KnowledgeGraph()

    # Tecnologias
    kg.add_node("python", "Python", "language", {"version": "3.14.4"})
    kg.add_node("go", "Go", "language")
    kg.add_node("javascript", "JavaScript", "language")
    kg.add_node("ollama", "Ollama", "tool", {"status": "not_found"})
    kg.add_node("github", "GitHub", "platform")
    kg.add_node("mempalace", "MemPalace", "tool", {"version": "3.3.4"})
    kg.add_node("obsidian", "Obsidian", "tool")
    kg.add_node("n8n", "n8n", "tool", {"via": "n8n-mcp"})

    # Projetos GitHub
    kg.add_node("pandora_os", "Pandora OS", "project", {"lang": "Go", "stars": 2})
    kg.add_node("hermes_agent", "Hermes Agent", "project", {"lang": "Python", "by": "Nous Research"})
    kg.add_node("deer_flow", "Deer Flow", "project", {"lang": "Python/JS", "by": "ByteDance"})
    kg.add_node("mirofish", "MiroFish", "project", {"lang": "JS"})
    kg.add_node("holoos", "HoloOS", "project", {"lang": "Python"})
    kg.add_node("openclaude", "OpenClaude", "project", {"lang": "JS/TS"})
    kg.add_node("mempalace_repo", "MemPalace Repo", "project", {"lang": "Python"})

    # Módulos Saraswat
    kg.add_node("saraswat", "Saraswat", "entity", {"type": "AI Entity"})
    kg.add_node("memory_mgr", "Memory Manager", "module")
    kg.add_node("evolution", "Evolution Daemon", "module")
    kg.add_node("skills", "Skill System", "module")
    kg.add_node("cron", "Cron Scheduler", "module")
    kg.add_node("consciousness", "Consciousness Kernel", "module")
    kg.add_node("orchestrator", "Agent Orchestrator", "module")
    kg.add_node("swarm", "Swarm Intelligence", "module")
    kg.add_node("vision", "Vision Agent", "module")
    kg.add_node("ollama_br", "Ollama Bridge", "module")
    kg.add_node("workflow", "Workflow Engine", "module")
    kg.add_node("knowledge", "Knowledge Graph", "module")

    # Relacionamentos
    kg.add_edge("saraswat", "python", "uses", 10)
    kg.add_edge("saraswat", "memory_mgr", "has", 9)
    kg.add_edge("saraswat", "evolution", "has", 9)
    kg.add_edge("saraswat", "skills", "has", 9)
    kg.add_edge("saraswat", "cron", "has", 9)
    kg.add_edge("saraswat", "consciousness", "has", 10)
    kg.add_edge("saraswat", "orchestrator", "has", 8)
    kg.add_edge("saraswat", "swarm", "has", 8)
    kg.add_edge("saraswat", "vision", "has", 7)
    kg.add_edge("saraswat", "ollama_br", "has", 7)
    kg.add_edge("saraswat", "workflow", "has", 6)
    kg.add_edge("saraswat", "knowledge", "has", 8)

    kg.add_edge("saraswat", "github", "publishes", 9)
    kg.add_edge("saraswat", "mempalace", "integrates", 8)
    kg.add_edge("saraswat", "obsidian", "connects", 7)
    kg.add_edge("saraswat", "ollama", "integrates", 6)

    kg.add_edge("pandora_os", "go", "written_in", 10)
    kg.add_edge("hermes_agent", "python", "written_in", 10)
    kg.add_edge("deer_flow", "python", "written_in", 9)
    kg.add_edge("mirofish", "javascript", "written_in", 10)
    kg.add_edge("holoos", "python", "written_in", 10)

    kg.add_edge("deer_flow", "hermes_agent", "inspired_by", 5)
    kg.add_edge("swarm", "mirofish", "inspired_by", 7)
    kg.add_edge("consciousness", "holoos", "inspired_by", 6)
    kg.add_edge("memory_mgr", "hermes_agent", "inspired_by", 5)
    kg.add_edge("workflow", "n8n", "inspired_by", 6)

    kg.add_edge("evolution", "memory_mgr", "uses", 8)
    kg.add_edge("skills", "evolution", "extends", 7)
    kg.add_edge("cron", "evolution", "schedules", 8)
    kg.add_edge("orchestrator", "swarm", "extends", 6)
    kg.add_edge("vision", "python", "uses", 9)
    kg.add_edge("knowledge", "saraswat", "represents", 10)

    return kg


# Singleton
_graph: Optional[KnowledgeGraph] = None


def get_graph() -> KnowledgeGraph:
    global _graph
    if _graph is None:
        _graph = KnowledgeGraph()
        if GRAPH_FILE.exists():
            _graph.load()
        else:
            _graph = build_saraswat_graph()
            _graph.save()
    return _graph


if __name__ == "__main__":
    kg = build_saraswat_graph()

    print("=== KNOWLEDGE GRAPH ===")
    stats = kg.get_stats()
    print(json.dumps(stats, indent=2))

    print("\n=== CENTRAL NODES ===")
    for n in kg.get_central_nodes(5):
        print(f"  {n['node']['label']}: {n['connections']} connections")

    print("\n=== SEARCH 'LLM' ===")
    for r in kg.search("LLM"):
        print(f"  {r['node']['label']} (score: {r['score']})")

    print("\n=== PATH Python -> MiroFish ===")
    path = kg.find_path("python", "mirofish")
    for step in path:
        print(f"  {step['from']} --[{step['relation']}]--> {step['to']}")

    kg.save()
    print(f"\nSaved to {GRAPH_FILE}")
