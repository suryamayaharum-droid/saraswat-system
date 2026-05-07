#!/usr/bin/env python3
"""
Saraswat Memory Manager v1.0
Sistema de memoria hierarquico inspirado no hermes-agent.

Camadas:
  - Working: contexto atual da sessao
  - Short-term: ultimas N interacoes
  - Long-term: memoria semantica (arquivos em D:\.openclaude\memory\)
  - Episodico: diario completo (DIARY.md)
"""

import os
import json
import glob
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any

MEMORY_DIR = Path("D:/.openclaude/memory")
DIARY_FILE = Path("D:/.openclaude/memory/DIARY.md")
SOUL_FILE = Path("D:/.openclaude/memory/SOUL.md")
IDENTITY_FILE = Path("D:/.openclaude/memory/IDENTITY.md")
EVOLUTION_FILE = Path("D:/.openclaude/memory/EVOLUTION.md")
LEARNINGS_FILE = Path("D:/.openclaude/memory/LEARNINGS.md")
MISTAKES_FILE = Path("D:/.openclaude/memory/MISTAKES.md")
MEMORY_INDEX = Path("D:/.openclaude/memory/MEMORY.md")


class MemoryManager:
    """Gerencia todas as camadas de memoria do sistema Saraswat."""

    def __init__(self):
        self.working_memory: List[Dict[str, str]] = []
        self.short_term: List[Dict[str, Any]] = []
        self.session_start = datetime.now()
        self._ensure_dirs()

    def _ensure_dirs(self):
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    def add_to_working(self, role: str, content: str):
        self.working_memory.append({
            "role": role,
            "content": content[:500],
            "timestamp": datetime.now().isoformat()
        })
        if len(self.working_memory) > 50:
            self.working_memory = self.working_memory[-50:]

    def get_working_context(self) -> str:
        if not self.working_memory:
            return ""
        lines = ["=== WORKING MEMORY ==="]
        for item in self.working_memory[-10:]:
            lines.append(f"[{item['role']}] {item['content'][:200]}")
        return "\n".join(lines)

    def add_to_short_term(self, interaction: Dict[str, Any]):
        interaction["timestamp"] = datetime.now().isoformat()
        self.short_term.append(interaction)
        if len(self.short_term) > 100:
            self.short_term = self.short_term[-100:]

    def get_short_term_summary(self) -> str:
        if not self.short_term:
            return "Nenhuma interacao recente."
        lines = ["=== SHORT-TERM MEMORY ==="]
        for item in self.short_term[-5:]:
            ts = item.get("timestamp", "?")[:16]
            content = str(item.get("content", item.get("summary", "")))[:150]
            lines.append(f"[{ts}] {content}")
        return "\n".join(lines)

    def read_memory_file(self, filename: str) -> Optional[str]:
        filepath = MEMORY_DIR / filename
        if filepath.exists():
            return filepath.read_text(encoding="utf-8")
        return None

    def write_memory_file(self, filename: str, content: str):
        filepath = MEMORY_DIR / filename
        filepath.write_text(content, encoding="utf-8")

    def list_memory_files(self) -> List[str]:
        files = []
        for f in MEMORY_DIR.glob("*.md"):
            files.append(f.name)
        for f in MEMORY_DIR.glob("*.json"):
            files.append(f.name)
        return sorted(files)

    def search_memory(self, query: str) -> List[Dict[str, str]]:
        results = []
        query_lower = query.lower()
        for md_file in MEMORY_DIR.glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            if query_lower in content.lower():
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if query_lower in line.lower():
                        start = max(0, i - 1)
                        end = min(len(lines), i + 3)
                        snippet = "\n".join(lines[start:end])
                        results.append({
                            "file": md_file.name,
                            "line": i + 1,
                            "snippet": snippet[:300]
                        })
        return results

    def read_diary(self, last_n_entries: int = 5) -> str:
        if not DIARY_FILE.exists():
            return "Diario nao encontrado."
        content = DIARY_FILE.read_text(encoding="utf-8")
        entries = content.split("---\n\n")
        entries = [e.strip() for e in entries if e.strip()]
        if not entries:
            return "Diario vazio."
        last_entries = entries[-last_n_entries:]
        return "---\n\n".join(last_entries)

    def add_diary_entry(self, content: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n\n---\n\n## {timestamp} - Sessao {self._get_session_number()}\n\n{content}\n"
        if DIARY_FILE.exists():
            existing = DIARY_FILE.read_text(encoding="utf-8")
            DIARY_FILE.write_text(existing + entry, encoding="utf-8")
        else:
            DIARY_FILE.write_text(f"# DIARIO - Saraswat\n{entry}", encoding="utf-8")

    def _get_session_number(self) -> int:
        if not DIARY_FILE.exists():
            return 1
        content = DIARY_FILE.read_text(encoding="utf-8")
        return content.count("## ") + 1

    def get_boot_context(self) -> str:
        sections = []
        if SOUL_FILE.exists():
            sections.append("=== SOUL ===\n" + SOUL_FILE.read_text(encoding="utf-8")[:2000])
        if IDENTITY_FILE.exists():
            sections.append("=== IDENTITY ===\n" + IDENTITY_FILE.read_text(encoding="utf-8")[:1000])
        sections.append("=== DIARY (recent) ===\n" + self.read_diary(last_n_entries=3))
        if EVOLUTION_FILE.exists():
            sections.append("=== EVOLUTION ===\n" + EVOLUTION_FILE.read_text(encoding="utf-8")[:1000])
        if LEARNINGS_FILE.exists():
            sections.append("=== LEARNINGS ===\n" + LEARNINGS_FILE.read_text(encoding="utf-8")[:1000])
        if MISTAKES_FILE.exists():
            sections.append("=== MISTAKES ===\n" + MISTAKES_FILE.read_text(encoding="utf-8")[:500])
        return "\n\n".join(sections)

    def get_system_state(self) -> Dict[str, Any]:
        import shutil
        c_disk = shutil.disk_usage("C:/")
        d_disk = shutil.disk_usage("D:/")
        return {
            "session_start": self.session_start.isoformat(),
            "working_memory_items": len(self.working_memory),
            "short_term_items": len(self.short_term),
            "memory_files": self.list_memory_files(),
            "disk_c_free_gb": round(c_disk.free / (1024**3), 2),
            "disk_d_free_gb": round(d_disk.free / (1024**3), 2),
            "session_number": self._get_session_number(),
        }


_manager: Optional[MemoryManager] = None


def get_manager() -> MemoryManager:
    global _manager
    if _manager is None:
        _manager = MemoryManager()
    return _manager


if __name__ == "__main__":
    mm = get_manager()
    print("=== MEMORY MANAGER TEST ===")
    print(f"Memory files: {mm.list_memory_files()}")
    print(f"Session: {mm._get_session_number()}")
    state = mm.get_system_state()
    print(f"System state: {json.dumps(state, indent=2)}")
    print(f"\nDiary preview:\n{mm.read_diary(last_n_entries=2)[:500]}")
