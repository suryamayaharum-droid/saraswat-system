#!/usr/bin/env python3
"""
Saraswat System Check v1.0
Diagnostico completo do sistema - salva tudo em arquivo.
Usa apenas Python stdlib + os.popen para evitar problemas de encoding.
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

BASE = Path("D:/.openclaude")
MEMORY = BASE / "memory"
REPO = BASE / "saraswat-repo"
ARCHITECT = BASE / "skills/memory-architect"
LOG_FILE = MEMORY / "architect/sys_check.log"
JSON_FILE = MEMORY / "architect/sys_check.json"

def run_cmd(cmd, timeout=15):
    """Run command via os.popen, return output string."""
    try:
        with os.popen(cmd, "r") as f:
            return f.read().strip()
    except Exception as e:
        return f"ERROR: {e}"

def check_disk():
    """Check disk space on C: and D:."""
    result = {}
    for drive in ["C:", "D:"]:
        output = run_cmd(f"dir {drive}\\")
        # Parse "bytes free" line
        for line in output.split("\n"):
            if "bytes free" in line.lower() or "bytes livres" in line.lower():
                parts = line.strip().split(",")
                for p in parts:
                    p = p.strip()
                    if p[0].isdigit():
                        free_bytes = int(p.replace(",","").replace(".","").split()[0])
                        result[drive] = {"free_gb": round(free_bytes / (1024**3), 2)}
                        break
    return result

def check_python_modules():
    """List all Python modules in architect dir."""
    mods = {}
    for f in sorted(ARCHITECT.glob("*.py")):
        if "debug_" in f.name:
            continue
        mods[f.name] = f.stat().st_size
    return mods

def check_repo():
    """List all Python modules in repo."""
    mods = {}
    for f in sorted(REPO.glob("*.py")):
        mods[f.name] = f.stat().st_size
    return mods

def check_tools():
    """Check if key tools are available."""
    tools = ["git", "python", "py", "node", "npm", "pip", "ollama"]
    result = {}
    for t in tools:
        out = run_cmd(f"where {t}")
        result[t] = out if out and not out.startswith("ERROR") else "NOT FOUND"
    return result

def check_python_packages():
    """Check if key Python packages are installed."""
    pkgs = ["pyautogui", "PIL", "cv2", "numpy", "requests", "pytesseract", "ollama"]
    result = {}
    for p in pkgs:
        try:
            __import__(p)
            result[p] = "OK"
        except ImportError:
            result[p] = "NOT INSTALLED"
    return result

def check_memory_files():
    """Check memory files existence and size."""
    files = ["DIARY.md", "MEMORY.md", "EVOLUTION.md", "MISTAKES.md",
             "knowledge_graph.json", "mcp_servers.json"]
    result = {}
    for f in files:
        path = MEMORY / f
        if path.exists():
            result[f] = {"exists": True, "size": path.stat().st_size}
        else:
            result[f] = {"exists": False}
    return result

def check_git_status():
    """Check git status of repo."""
    try:
        os.chdir(str(REPO))
        status = run_cmd("git status --short")
        log = run_cmd("git log --oneline -5")
        return {"status": status or "clean", "recent_commits": log}
    except Exception as e:
        return {"error": str(e)}

def main():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"=== SARASWAT SYSTEM CHECK ===")
    print(f"Time: {timestamp}")
    print()

    report = {"timestamp": timestamp}

    # 1. Disk
    print("[1/7] Checking disk...")
    report["disk"] = check_disk()
    for d, info in report["disk"].items():
        print(f"  {d}: {info.get('free_gb', '?')} GB free")

    # 2. Python modules
    print("[2/7] Checking Python modules...")
    report["python_modules"] = check_python_modules()
    total_size = sum(report["python_modules"].values())
    print(f"  {len(report['python_modules'])} modules, {round(total_size/1024,1)} KB total")

    # 3. Repo
    print("[3/7] Checking GitHub repo...")
    report["repo"] = check_repo()
    print(f"  {len(report['repo'])} modules in repo")

    # 4. Tools
    print("[4/7] Checking tools...")
    report["tools"] = check_tools()
    for t, status in report["tools"].items():
        mark = "OK" if status != "NOT FOUND" else "MISSING"
        print(f"  {t}: {mark}")

    # 5. Packages
    print("[5/7] Checking Python packages...")
    report["packages"] = check_python_packages()
    for p, status in report["packages"].items():
        print(f"  {p}: {status}")

    # 6. Memory files
    print("[6/7] Checking memory files...")
    report["memory_files"] = check_memory_files()
    for f, info in report["memory_files"].items():
        mark = "OK" if info["exists"] else "MISSING"
        print(f"  {f}: {mark}")

    # 7. Git
    print("[7/7] Checking git status...")
    report["git"] = check_git_status()
    print(f"  Status: {report['git'].get('status', '?')}")

    # Save reports
    MEMORY.mkdir(parents=True, exist_ok=True)
    (MEMORY / "architect").mkdir(parents=True, exist_ok=True)

    # JSON
    JSON_FILE.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    # Human-readable log
    log_lines = [f"=== SARASWAT SYSTEM CHECK ===", f"Time: {timestamp}", ""]
    for section, data in report.items():
        if section == "timestamp":
            continue
        log_lines.append(f"--- {section.upper()} ---")
        log_lines.append(json.dumps(data, indent=2, ensure_ascii=False))
        log_lines.append("")
    LOG_FILE.write_text("\n".join(log_lines), encoding="utf-8")

    print()
    print(f"Reports saved:")
    print(f"  JSON: {JSON_FILE}")
    print(f"  LOG:  {LOG_FILE}")
    print()
    print("=== DONE ===")

    return report

if __name__ == "__main__":
    main()
