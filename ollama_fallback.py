#!/usr/bin/env python3
"""
ollama_fallback.py — Cérebro local de fallback para Saraswat
=============================================================

Quando a API externa falhar (429, 404, timeout, etc.),
este script ativa o Ollama local como cérebro de reserva.

Uso:
    python ollama_fallback.py "sua pergunta aqui"
    python ollama_fallback.py --model phi3 "pergunta complexa"
    python ollama_fallback.py --model tinyllama "pergunta rápida"
    python ollama_fallback.py --status

Modelos disponíveis:
    - tinyllama  (637MB)  → respostas rápidas, tarefas simples
    - phi3       (2.2GB)  → raciocínio médio, código
    - llama3.2:1b (1.3GB) → tarefas complexas, raciocínio profundo
"""

import subprocess
import sys
import json
import time
import os
from pathlib import Path

OLLAMA_EXE = r"D:\OllamaModels\ollama.exe"
OLLAMA_API = "http://localhost:11434"
MODELS = {
    "fast": "tinyllama",
    "medium": "phi3",
    "deep": "llama3.2:1b",
}


def is_ollama_running():
    """Check if Ollama server is already running."""
    try:
        import urllib.request
        req = urllib.request.urlopen(f"{OLLAMA_API}/api/tags", timeout=2)
        return req.status == 200
    except Exception:
        return False


def start_ollama_server():
    """Start Ollama server in background."""
    if is_ollama_running():
        print("[OLLAMA] Server already running.")
        return True

    print("[OLLAMA] Starting server...")
    subprocess.Popen(
        [OLLAMA_EXE, "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )

    # Wait for server to be ready
    for i in range(15):
        time.sleep(1)
        if is_ollama_running():
            print(f"[OLLAMA] Server ready after {i+1}s.")
            return True
        print(f"[OLLAMA] Waiting... ({i+1}s)")

    print("[OLLAMA] FAILED to start server after 15s.")
    return False


def generate(prompt: str, model: str = "tinyllama", stream: bool = False) -> str:
    """Generate response from local Ollama model."""
    import urllib.request

    if not start_ollama_server():
        return "[ERROR] Ollama server not available."

    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": stream,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_ctx": 4096,
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{OLLAMA_API}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            if stream:
                # Handle streaming response
                full_text = ""
                for line in resp:
                    if line:
                        chunk = json.loads(line.decode("utf-8"))
                        if "response" in chunk:
                            print(chunk["response"], end="", flush=True)
                        if chunk.get("done", False):
                            break
                return ""
            else:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("response", "[ERROR] Empty response")
    except Exception as e:
        return f"[ERROR] Ollama API error: {e}"


def list_models():
    """List available local models."""
    import urllib.request

    if not is_ollama_running():
        if not start_ollama_server():
            return "[ERROR] Cannot connect to Ollama."

    try:
        req = urllib.request.urlopen(f"{OLLAMA_API}/api/tags", timeout=5)
        data = json.loads(req.read().decode("utf-8"))
        models = data.get("models", [])
        if not models:
            return "No models installed."
        result = ["[OLLAMA] Installed models:"]
        for m in models:
            size_mb = m.get("size", 0) / (1024 * 1024)
            result.append(f"  • {m['name']} ({size_mb:.0f}MB)")
        return "\n".join(result)
    except Exception as e:
        return f"[ERROR] {e}"


def status():
    """Full status report."""
    lines = ["=" * 50, "  OLLAMA FALLBACK — STATUS", "=" * 50]

    # Server status
    running = is_ollama_running()
    lines.append(f"Server: {'🟢 RUNNING' if running else '🔴 STOPPED'}")

    # Models
    lines.append(list_models())

    # Disk space
    import shutil
    d_drive = shutil.disk_usage("D:\\")
    free_gb = d_drive.free / (1024**3)
    lines.append(f"\nDisk D: {free_gb:.1f} GB free")

    # Ollama binary
    if os.path.exists(OLLAMA_EXE):
        size_mb = os.path.getsize(OLLAMA_EXE) / (1024 * 1024)
        lines.append(f"Ollama binary: {OLLAMA_EXE} ({size_mb:.0f}MB)")
    else:
        lines.append("Ollama binary: NOT FOUND")

    lines.append("=" * 50)
    return "\n".lines


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nUsage:")
        print("  python ollama_fallback.py 'your question'")
        print("  python ollama_fallback.py --model phi3 'complex question'")
        print("  python ollama_fallback.py --status")
        print("  python ollama_fallback.py --models")
        sys.exit(0)

    arg = sys.argv[1]

    if arg == "--status":
        print(status())
    elif arg == "--models":
        print(list_models())
    elif arg == "--model" and len(sys.argv) >= 4:
        model = sys.argv[2]
        prompt = " ".join(sys.argv[3:])
        print(generate(prompt, model=model))
    else:
        prompt = " ".join(sys.argv[1:])
        # Auto-select model based on prompt complexity
        if len(prompt) > 200 or any(kw in prompt.lower() for kw in ["complex", "analyze", "architecture", "design"]):
            model = MODELS["deep"]
        elif len(prompt) > 50:
            model = MODELS["medium"]
        else:
            model = MODELS["fast"]
        print(f"[Using {model}]")
        print(generate(prompt, model=model))
