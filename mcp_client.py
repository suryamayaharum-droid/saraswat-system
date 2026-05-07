#!/usr/bin/env python3
"""
Saraswat MCP Client v1.0
Cliente para Model Context Protocol (MCP).

Permite conectar a servidores MCP externos para expandir capacidades:
- File system access
- Web search
- Database queries
- Custom tools

Inspirado no ecossistema MCP 2026.
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict

# ─── Data Models ───────────────────────────────────────────────

@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MCPServer:
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    status: str = "disconnected"
    tools: List[MCPTool] = field(default_factory=list)
    pid: Optional[int] = None

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "command": self.command,
            "args": self.args,
            "status": self.status,
            "tools": [asdict(t) for t in self.tools],
            "pid": self.pid,
        }


# ─── MCP Client ────────────────────────────────────────────────

class SaraswatMCPClient:
    """Cliente MCP para conectar a servidores externos."""

    def __init__(self, config_path: Optional[Path] = None):
        self.servers: Dict[str, MCPServer] = {}
        self.config_path = config_path or Path(__file__).parent.parent / "memory" / "mcp_servers.json"
        self._processes: Dict[str, subprocess.Popen] = {}

    def register_server(self, name: str, command: str, args: List[str] = None,
                        env: Dict[str, str] = None) -> MCPServer:
        """Registra um servidor MCP."""
        server = MCPServer(
            name=name,
            command=command,
            args=args or [],
            env=env or {},
        )
        self.servers[name] = server
        return server

    def register_defaults(self):
        """Registra servidores MCP padrão conhecidos."""
        defaults = [
            MCPServer("filesystem", "npx", ["-y", "@modelcontextprotocol/server-filesystem", "D:/"]),
            MCPServer("github_mcp", "npx", ["-y", "@modelcontextprotocol/server-github"]),
            MCPServer("memory_mcp", "npx", ["-y", "@modelcontextprotocol/server-memory"]),
            MCPServer("fetch", "npx", ["-y", "@modelcontextprotocol/server-fetch"]),
            MCPServer("sqlite", "npx", ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", "D:/.openclaude/memory/saraswat.db"]),
            MCPServer("puppeteer", "npx", ["-y", "@modelcontextprotocol/server-puppeteer"]),
        ]
        for s in defaults:
            self.servers[s.name] = s
        return self

    def connect(self, name: str) -> bool:
        """Conecta a um servidor MCP."""
        if name not in self.servers:
            print(f"[MCP] Servidor '{name}' não registrado")
            return False

        server = self.servers[name]
        try:
            cmd = [server.command] + server.args
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**server.env},
                text=True,
            )
            server.pid = proc.pid
            server.status = "connected"
            self._processes[name] = proc
            print(f"[MCP] Conectado a '{name}' (PID: {proc.pid})")
            return True
        except FileNotFoundError:
            server.status = "not_found"
            print(f"[MCP] Comando '{server.command}' não encontrado para '{name}'")
            return False
        except Exception as e:
            server.status = "error"
            print(f"[MCP] Erro conectando a '{name}': {e}")
            return False

    def disconnect(self, name: str):
        """Desconecta de um servidor MCP."""
        if name in self._processes:
            proc = self._processes[name]
            proc.terminate()
            proc.wait(timeout=5)
            del self._processes[name]
        if name in self.servers:
            self.servers[name].status = "disconnected"
            self.servers[name].pid = None

    def disconnect_all(self):
        """Desconecta de todos os servidores."""
        for name in list(self._processes.keys()):
            self.disconnect(name)

    def list_servers(self) -> List[Dict]:
        """Lista todos os servidores registrados."""
        return [s.to_dict() for s in self.servers.values()]

    def get_status(self) -> Dict[str, str]:
        """Retorna status de todos os servidores."""
        return {name: s.status for name, s in self.servers.items()}

    def save_config(self):
        """Salva configuração dos servidores."""
        data = {"servers": {name: s.to_dict() for name, s in self.servers.items()}}
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def load_config(self):
        """Carrega configuração dos servidores."""
        if self.config_path.exists():
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
            for name, sdata in data.get("servers", {}).items():
                self.servers[name] = MCPServer(
                    name=sdata["name"],
                    command=sdata["command"],
                    args=sdata.get("args", []),
                    status="disconnected",
                )

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde de todos os servidores conectados."""
        results = {}
        for name, proc in self._processes.items():
            if proc.poll() is None:
                results[name] = {"status": "running", "pid": proc.pid}
            else:
                results[name] = {"status": "crashed", "returncode": proc.returncode}
                self.servers[name].status = "crashed"
        return results


# ─── MCP Tool Registry ─────────────────────────────────────────

class MCPToolRegistry:
    """Registry de ferramentas MCP disponíveis."""

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def register(self, server: str, tool: MCPTool):
        """Registra uma ferramenta de um servidor."""
        key = f"{server}/{tool.name}"
        self.tools[key] = {
            "server": server,
            "name": tool.name,
            "description": tool.description,
            "schema": tool.input_schema,
        }

    def find(self, query: str) -> List[Dict]:
        """Busca ferramentas por nome ou descrição."""
        query_lower = query.lower()
        results = []
        for key, tool in self.tools.items():
            if query_lower in tool["name"].lower() or query_lower in tool["description"].lower():
                results.append(tool)
        return results

    def list_all(self) -> List[Dict]:
        """Lista todas as ferramentas."""
        return list(self.tools.values())


# ─── Main ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== MCP CLIENT ===\n")

    client = SaraswatMCPClient()
    client.register_defaults()

    print("Registered servers:")
    for s in client.list_servers():
        args_preview = " ".join(s["args"][:2]) + "..." if s["args"] else ""
        print(f"  {s['name']:15s} -> {s['command']} {args_preview}")

    print(f"\nTotal: {len(client.servers)} servers registered")
    print(f"Config path: {client.config_path}")

    # Save config
    client.save_config()
    print("Config saved.")

    # Health check (nothing connected yet)
    status = client.get_status()
    print(f"\nStatus: {json.dumps(status)}")

    print("\n=== MCP CLIENT OK ===")
