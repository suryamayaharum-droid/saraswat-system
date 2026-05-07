#!/usr/bin/env python3
"""
Saraswat Ollama Bridge v1.0
Ponte para Ollama - modelos LLM locais.

Detecta automaticamente o Ollama, lista modelos disponíveis
e fornece uma interface unificada para geração de texto.

Quantizacao de pensamento:
  - Tarefa simples (< 50 chars) -> tinyllama (608MB, ~1-3s)
  - Tarefa media (50-200 chars) -> tinyllama com contexto expandido (~3-5s)
  - Tarefa complexa (> 200 chars) -> llama3.2:1b (1.2GB, ~5-15s)
  - phi3 -> DESATIVADO (erro 500, requer mais RAM/GPU)
"""

import json
import subprocess
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

MEMORY_DIR = Path("D:/.openclaude/memory")


class OllamaBridge:
    """Ponte para Ollama - gerencia modelos locais."""

    def __init__(self):
        self.ollama_path: Optional[str] = None
        self.is_running: bool = False
        self.models: List[Dict[str, Any]] = []
        self._find_ollama()
        self._check_status()

    def _find_ollama(self):
        """Encontra o executável do Ollama."""
        search_paths = [
            "C:/Users/harum/AppData/Local/Ollama/ollama.exe",
            "C:/Program Files/Ollama/ollama.exe",
            "D:/Ollama/ollama.exe",
            "ollama"  # PATH
        ]
        for path in search_paths:
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    self.ollama_path = path
                    return
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

    def _check_status(self):
        """Verifica se o Ollama está rodando."""
        if not self.ollama_path:
            return
        try:
            result = subprocess.run(
                [self.ollama_path, "list"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                self.is_running = True
                self._parse_models(result.stdout)
        except (subprocess.TimeoutExpired, Exception):
            self.is_running = False

    def _parse_models(self, output: str):
        """Parse da saída de 'ollama list'."""
        self.models = []
        lines = output.strip().split("\n")
        for line in lines[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 2:
                self.models.append({
                    "name": parts[0],
                    "size": parts[2] if len(parts) > 2 else "unknown",
                    "modified": parts[-1] if len(parts) > 3 else "unknown",
                })

    def start_server(self) -> bool:
        """Inicia o servidor Ollama em background."""
        if not self.ollama_path:
            return False
        try:
            subprocess.Popen(
                [self.ollama_path, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            time.sleep(3)
            self._check_status()
            return self.is_running
        except Exception:
            return False

    def stop_server(self) -> bool:
        """Para o servidor Ollama."""
        if not self.ollama_path:
            return False
        try:
            if os.name == 'nt':
                subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], capture_output=True, timeout=5)
            else:
                subprocess.run(["pkill", "ollama"], capture_output=True, timeout=5)
            self.is_running = False
            return True
        except Exception:
            return False

    def generate(self, prompt: str, model: str = None, timeout: int = 30) -> Dict[str, Any]:
        """Gera texto usando um modelo local."""
        if not self.is_running or not self.ollama_path:
            return {"error": "Ollama not running", "response": ""}

        # Quantização de pensamento: escolher modelo baseado na complexidade
        if not model:
            model = self._select_model(prompt)

        try:
            start_time = time.time()
            result = subprocess.run(
                [self.ollama_path, "run", model, prompt],
                capture_output=True, text=True, timeout=timeout
            )
            elapsed = time.time() - start_time

            return {
                "model": model,
                "response": result.stdout.strip(),
                "error": result.stderr.strip() if result.returncode != 0 else None,
                "elapsed_seconds": round(elapsed, 2),
                "prompt_length": len(prompt),
                "response_length": len(result.stdout.strip()),
                "timestamp": datetime.now().isoformat(),
            }
        except subprocess.TimeoutExpired:
            return {"error": "Timeout", "response": "", "model": model}
        except Exception as e:
            return {"error": str(e), "response": "", "model": model}

    def _select_model(self, prompt: str) -> str:
        """Seleciona o modelo ideal baseado na complexidade da tarefa."""
        length = len(prompt)

        available = [m["name"] for m in self.models]

        if length <= 50:
            # Tarefa simples -> modelo pequeno
            for m in available:
                if "tinyllama" in m:
                    return m
        elif length <= 200:
            # Tarefa média
            for m in available:
                if "tinyllama" in m:
                    return m

        # Tarefa complexa -> modelo maior
        for m in available:
            if "llama3" in m or "llama-3" in m:
                return m

        # Fallback para qualquer modelo disponível
        return available[0] if available else "tinyllama"

    def pull_model(self, model_name: str) -> bool:
        """Baixa um modelo do Ollama."""
        if not self.ollama_path:
            return False
        try:
            result = subprocess.run(
                [self.ollama_path, "pull", model_name],
                capture_output=True, text=True, timeout=600
            )
            self._check_status()
            return result.returncode == 0
        except Exception:
            return False

    def get_status(self) -> Dict[str, Any]:
        """Retorna status do Ollama."""
        return {
            "found": self.ollama_path is not None,
            "path": self.ollama_path,
            "running": self.is_running,
            "models": self.models,
            "model_count": len(self.models),
        }


_bridge: Optional[OllamaBridge] = None


def get_bridge() -> OllamaBridge:
    global _bridge
    if _bridge is None:
        _bridge = OllamaBridge()
    return _bridge


if __name__ == "__main__":
    bridge = get_bridge()
    status = bridge.get_status()

    print("=== OLLAMA BRIDGE ===")
    print(json.dumps(status, indent=2))

    if status["running"] and status["models"]:
        print("\n=== TEST GENERATION ===")
        result = bridge.generate("Hello, who are you?", timeout=15)
        print(json.dumps(result, indent=2))
