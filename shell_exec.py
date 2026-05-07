#!/usr/bin/env python3
"""
Saraswat Shell Exec v1.0
Executor de comandos que SEMPRE salva output em arquivo.
Solucao definitiva para o problema de output perdido no Claude Code.

O Claude Code perde output de subprocessos PowerShell/cmd.
Este modulo contorna isso salvando tudo em D:/.openclaude/memory/architect/logs/

Uso:
    from shell_exec import run
    result = run("dir C:")
    print(result.stdout)

    # ou via CLI:
    python shell_exec.py "dir C:"
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any

LOG_DIR = Path("D:/.openclaude/memory/architect/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ExecResult:
    command: str
    returncode: int
    stdout: str
    stderr: str
    duration_sec: float
    timestamp: str
    log_file: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def __str__(self) -> str:
        lines = [
            f"Command: {self.command}",
            f"Return: {self.returncode}",
            f"Duration: {self.duration_sec:.2f}s",
            f"Log: {self.log_file}",
        ]
        if self.stdout:
            lines.append(f"--- STDOUT ---\n{self.stdout[:2000]}")
        if self.stderr:
            lines.append(f"--- STDERR ---\n{self.stderr[:1000]}")
        return "\n".join(lines)


def run(command: str, timeout: int = 60, shell: bool = True,
        capture: bool = True, env: Optional[Dict] = None) -> ExecResult:
    """
    Executa um comando e salva output em arquivo.

    Args:
        command: Comando a executar
        timeout: Timeout em segundos
        shell: Usar shell
        capture: Capturar output

    Returns:
        ExecResult com stdout, stderr, returncode, e caminho do log
    """
    ts = datetime.now()
    ts_str = ts.strftime("%Y%m%d_%H%M%S")
    safe_cmd = "".join(c if c.isalnum() else "_" for c in command[:30])
    log_file = LOG_DIR / f"{ts_str}_{safe_cmd}.log"

    start = datetime.now()
    try:
        proc = subprocess.run(
            command,
            shell=shell,
            capture_output=capture,
            text=True,
            timeout=timeout,
            env=env or os.environ.copy(),
            encoding="utf-8",
            errors="replace",
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        returncode = proc.returncode
    except subprocess.TimeoutExpired:
        stdout = ""
        stderr = f"TIMEOUT after {timeout}s"
        returncode = -1
    except Exception as e:
        stdout = ""
        stderr = str(e)
        returncode = -2

    duration = (datetime.now() - start).total_seconds()

    result = ExecResult(
        command=command,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        duration_sec=round(duration, 2),
        timestamp=ts.strftime("%Y-%m-%d %H:%M:%S"),
        log_file=str(log_file),
    )

    # Save to log file
    log_content = str(result)
    log_file.write_text(log_content, encoding="utf-8")

    return result


def run_ps(script: str, timeout: int = 60) -> ExecResult:
    """Executa um script PowerShell e salva output."""
    return run(f'powershell -ExecutionPolicy Bypass -Command "{script}"', timeout=timeout)


def run_file(script_path: str, timeout: int = 120) -> ExecResult:
    """Executa um script file (.ps1, .py, .bat) e salva output."""
    p = Path(script_path)
    if not p.exists():
        return ExecResult(
            command=f"run_file({script_path})",
            returncode=-1,
            stdout="",
            stderr=f"File not found: {script_path}",
            duration_sec=0,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            log_file="",
        )

    ext = p.suffix.lower()
    if ext == ".ps1":
        return run(f'powershell -ExecutionPolicy Bypass -File "{script_path}"', timeout=timeout)
    elif ext == ".py":
        return run(f'python "{script_path}"', timeout=timeout)
    elif ext == ".bat" or ext == ".cmd":
        return run(f'cmd /c "{script_path}"', timeout=timeout)
    else:
        return run(f'"{script_path}"', timeout=timeout)


def run_many(commands: List[str], timeout: int = 60) -> List[ExecResult]:
    """Executa múltiplos comandos e retorna resultados."""
    return [run(cmd, timeout=timeout) for cmd in commands]


def get_logs_dir() -> Path:
    """Retorna o diretório de logs."""
    return LOG_DIR


def list_logs() -> List[Dict[str, Any]]:
    """Lista todos os logs gerados."""
    logs = []
    for f in sorted(LOG_DIR.glob("*.log"), reverse=True):
        stat = f.stat()
        logs.append({
            "file": str(f),
            "name": f.name,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        })
    return logs


def read_log(log_file: str) -> str:
    """Lê um arquivo de log."""
    p = Path(log_file)
    if p.exists():
        return p.read_text(encoding="utf-8")
    return f"Log not found: {log_file}"


def git_run(args: str, repo: str = "D:/.openclaude/saraswat-repo", timeout: int = 30) -> ExecResult:
    """Executa comando git no repo."""
    return run(f'cd /d "{repo}" && git {args}', timeout=timeout)


def git_push_all(message: str = "Saraswat auto-update") -> ExecResult:
    """Git add, commit e push."""
    repo = "D:/.openclaude/saraswat-repo"
    r1 = git_run("add -A", repo)
    if not r1.ok:
        return r1
    r2 = git_run(f'commit -m "{message}"', repo)
    # Commit pode falhar se nada mudou - ok
    r3 = git_run("push origin main", repo, timeout=60)
    return r3


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:])
        result = run(cmd)
        print(result)
    else:
        # Demo
        print("=== SHELL EXEC DEMO ===\n")

        r1 = run("dir C:\\")
        print(f"dir C: -> return={r1.returncode}, stdout_len={len(r1.stdout)}")

        r2 = run("python --version")
        print(f"python --version -> {r2.stdout.strip()}")

        r3 = run("git --version")
        print(f"git --version -> {r3.stdout.strip()}")

        r4 = run_ps("(Get-PSDrive C).Free / 1GB")
        print(f"PS disk check -> {r4.stdout.strip()}")

        print(f"\nLogs saved to: {LOG_DIR}")
        for log in list_logs()[:5]:
            print(f"  {log['name']}: {log['size']} bytes")
