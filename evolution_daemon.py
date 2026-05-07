#!/usr/bin/env python3
"""
Saraswat Evolution Daemon v1.0
Daemon de auto-evolução inspirado no pandora-os.

Responsabilidades:
  - Monitorar saúde do sistema (disco, memória, processos)
  - Auto-otimizar: limpar caches, liberar espaço
  - Evoluir: atualizar EVOLUTION.md, registrar aprendizados
  - Reportar: gerar relatórios periódicos

Three Laws of Self-Evolving AI:
  1. ENDURE (Segurança): Qualquer modificação mantém segurança e estabilidade
  2. EXCEL (Performance): Preservar ou melhorar performance
  3. EVOLVE (Evolução): Otimizar componentes internos autonomamente
"""

import os
import json
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Paths
MEMORY_DIR = Path("D:/.openclaude/memory")
EVOLUTION_FILE = MEMORY_DIR / "EVOLUTION.md"
LEARNINGS_FILE = MEMORY_DIR / "LEARNINGS.md"
MISTAKES_FILE = MEMORY_DIR / "MISTAKES.md"
STATE_FILE = MEMORY_DIR / "system_state.json"
LOG_FILE = MEMORY_DIR / "evolution_daemon.log"

# Thresholds
DISK_CRITICAL_GB = 1.0  # Abaixo de 1GB = crítico
DISK_WARNING_GB = 5.0    # Abaixo de 5GB = aviso


class EvolutionDaemon:
    """Daemon de auto-evolução do sistema Saraswat."""

    def __init__(self):
        self.cycle_count = 0
        self.last_check: Optional[datetime] = None
        self.issues_found: List[str] = []
        self.actions_taken: List[str] = []

    def log(self, message: str):
        """Log com timestamp."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {message}"
        print(line)
        # Append to log file
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    # ── System Health ──

    def check_disk_space(self) -> Dict[str, Any]:
        """Verifica espaço em disco."""
        results = {}
        for drive in ["C:", "D:"]:
            try:
                usage = shutil.disk_usage(drive)
                free_gb = round(usage.free / (1024**3), 2)
                total_gb = round(usage.total / (1024**3), 2)
                used_pct = round((usage.used / usage.total) * 100, 1)

                status = "ok"
                if free_gb < DISK_CRITICAL_GB:
                    status = "critical"
                elif free_gb < DISK_WARNING_GB:
                    status = "warning"

                results[drive] = {
                    "free_gb": free_gb,
                    "total_gb": total_gb,
                    "used_pct": used_pct,
                    "status": status
                }

                if status == "critical":
                    self.issues_found.append(f"DISCO {drive} CRÍTICO: {free_gb}GB livres")
                elif status == "warning":
                    self.issues_found.append(f"DISCO {drive} BAIXO: {free_gb}GB livres")
            except Exception as e:
                results[drive] = {"error": str(e)}

        return results

    def check_memory_files(self) -> Dict[str, Any]:
        """Verifica integridade dos arquivos de memória."""
        required_files = {
            "SOUL.md": MEMORY_DIR / "SOUL.md",
            "IDENTITY.md": MEMORY_DIR / "IDENTITY.md",
            "DIARY.md": MEMORY_DIR / "DIARY.md",
            "EVOLUTION.md": MEMORY_DIR / "EVOLUTION.md",
            "LEARNINGS.md": MEMORY_DIR / "LEARNINGS.md",
            "MISTAKES.md": MEMORY_DIR / "MISTAKES.md",
        }

        results = {}
        for name, path in required_files.items():
            exists = path.exists()
            size = path.stat().st_size if exists else 0
            results[name] = {"exists": exists, "size": size}
            if not exists:
                self.issues_found.append(f"ARQUIVO AUSENTE: {name}")

        return results

    def check_ollama(self) -> Dict[str, Any]:
        """Verifica status do Ollama."""
        result = {"status": "unknown", "models": []}
        try:
            proc = subprocess.run(
                ["powershell", "-Command", "ollama list 2>&1"],
                capture_output=True, text=True, timeout=10
            )
            output = proc.stdout + proc.stderr
            if "NAME" in output or "model" in output.lower():
                result["status"] = "running"
                # Parse model names
                for line in output.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("NAME") and not line.startswith("---"):
                        result["models"].append(line.split()[0] if line.split() else line)
            else:
                result["status"] = "not_running"
                self.issues_found.append("OLLAMA: não está rodando")
        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
        except Exception as e:
            result["status"] = f"error: {e}"

        return result

    # ── Self-Optimization ──

    def cleanup_temp_files(self) -> int:
        """Limpa arquivos temporários. Retorna bytes liberados."""
        freed = 0
        temp_dirs = [
            Path(os.environ.get("TEMP", "C:/Windows/Temp")),
            Path("C:/Windows/Temp"),
        ]

        for temp_dir in temp_dirs:
            if not temp_dir.exists():
                continue
            try:
                for item in temp_dir.iterdir():
                    try:
                        if item.is_file():
                            size = item.stat().st_size
                            item.unlink()
                            freed += size
                        elif item.is_dir():
                            size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                            shutil.rmtree(item, ignore_errors=True)
                            freed += size
                    except (PermissionError, OSError):
                        pass  # Arquivo em uso, pula
            except Exception:
                pass

        if freed > 0:
            freed_mb = round(freed / (1024**2), 2)
            self.actions_taken.append(f"LIMPEZA: {freed_mb}MB liberados de temp")
            return freed
        return 0

    def optimize_memory_files(self):
        """Otimiza arquivos de memória (remove duplicatas, formata)."""
        # Verifica se DIARY.md não está muito grande
        diary_path = MEMORY_DIR / "DIARY.md"
        if diary_path.exists():
            content = diary_path.read_text(encoding="utf-8")
            entries = content.count("## 20")  # Conta entradas
            if entries > 50:
                self.issues_found.append(
                    f"DIARY.md: {entries} entradas (considerar arquivar antigas)"
                )

    # ── Evolution ──

    def record_evolution(self, change: str, reason: str):
        """Registra uma mudança evolutiva."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n### {timestamp} — {change}\n**Razão:** {reason}\n"

        if EVOLUTION_FILE.exists():
            content = EVOLUTION_FILE.read_text(encoding="utf-8")
            # Adiciona após o último header de versão
            EVOLUTION_FILE.write_text(content + entry, encoding="utf-8")
        else:
            EVOLUTION_FILE.write_text(f"# 🧬 EVOLUTION.md\n{entry}", encoding="utf-8")

        self.actions_taken.append(f"EVOLUÇÃO registrada: {change}")

    def record_learning(self, learning: str, source: str = "auto"):
        """Registra um aprendizado."""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        entry = f"\n### {timestamp}\n- **Aprendizado:** {learning}\n- **Fonte:** {source}\n"

        if LEARNINGS_FILE.exists():
            content = LEARNINGS_FILE.read_text(encoding="utf-8")
            LEARNINGS_FILE.write_text(content + entry, encoding="utf-8")
        else:
            LEARNINGS_FILE.write_text(f"# 📚 LEARNINGS.md\n{entry}", encoding="utf-8")

    def record_mistake(self, mistake: str, fix: str):
        """Registra um erro para não repetir."""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        entry = f"\n### {timestamp}\n- **Erro:** {mistake}\n- **Correção:** {fix}\n"

        if MISTAKES_FILE.exists():
            content = MISTAKES_FILE.read_text(encoding="utf-8")
            MISTAKES_FILE.write_text(content + entry, encoding="utf-8")
        else:
            MISTAKES_FILE.write_text(f"# ❌ MISTAKES.md\n{entry}", encoding="utf-8")

    # ── Main Cycle ──

    def run_cycle(self) -> Dict[str, Any]:
        """Executa um ciclo completo de evolução."""
        self.cycle_count += 1
        self.last_check = datetime.now()
        self.issues_found = []
        self.actions_taken = []

        self.log(f"=== CICLO #{self.cycle_count} ===")

        # 1. Check disk
        disk = self.check_disk_space()
        self.log(f"Disk: C={disk.get('C:', {}).get('free_gb', '?')}GB | D={disk.get('D:', {}).get('free_gb', '?')}GB")

        # 2. Check memory files
        mem_files = self.check_memory_files()
        missing = [k for k, v in mem_files.items() if not v["exists"]]
        if missing:
            self.log(f"Missing files: {missing}")
        else:
            self.log("Memory files: OK")

        # 3. Check Ollama
        ollama = self.check_ollama()
        self.log(f"Ollama: {ollama['status']} | Models: {len(ollama.get('models', []))}")

        # 4. Self-optimization
        freed = self.cleanup_temp_files()
        if freed > 0:
            self.log(f"Cleanup: {round(freed/(1024**2), 2)}MB freed")

        self.optimize_memory_files()

        # 5. Save state
        state = {
            "cycle": self.cycle_count,
            "timestamp": self.last_check.isoformat(),
            "disk": disk,
            "ollama": ollama,
            "issues": self.issues_found,
            "actions": self.actions_taken,
        }
        STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

        # 6. Report
        if self.issues_found:
            self.log(f"ISSUES: {len(self.issues_found)}")
            for issue in self.issues_found:
                self.log(f"  ⚠ {issue}")

        if self.actions_taken:
            self.log(f"ACTIONS: {len(self.actions_taken)}")
            for action in self.actions_taken:
                self.log(f"  ✓ {action}")

        self.log(f"=== FIM CICLO #{self.cycle_count} ===")
        return state


# ── Singleton ──
_daemon: Optional[EvolutionDaemon] = None


def get_daemon() -> EvolutionDaemon:
    """Retorna instância singleton do EvolutionDaemon."""
    global _daemon
    if _daemon is None:
        _daemon = EvolutionDaemon()
    return _daemon


if __name__ == "__main__":
    daemon = get_daemon()
    state = daemon.run_cycle()
    print(json.dumps(state, indent=2, ensure_ascii=False))
