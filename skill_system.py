#!/usr/bin/env python3
"""
Saraswat Skill System v1.0
Sistema de skills inspirado no hermes-agent.

Skills são capacidades auto-contidas que o sistema pode aprender, armazenar e invocar.
Cada skill tem: nome, descrição, trigger, ação, e metadados.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Paths
SKILLS_DIR = Path("D:/.openclaude/skills")
SKILLS_INDEX = SKILLS_DIR / "SKILLS_INDEX.json"


class Skill:
    """Representa uma skill do sistema."""

    def __init__(
        self,
        name: str,
        description: str,
        trigger: str,
        action: str,
        category: str = "general",
        enabled: bool = True,
        metadata: Optional[Dict] = None,
    ):
        self.name = name
        self.description = description
        self.trigger = trigger  # Palavra-chave ou padrão que ativa a skill
        self.action = action  # O que a skill faz (prompt template ou código)
        self.category = category
        self.enabled = enabled
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
        self.use_count = 0
        self.last_used: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "trigger": self.trigger,
            "action": self.action,
            "category": self.category,
            "enabled": self.enabled,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "use_count": self.use_count,
            "last_used": self.last_used,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        skill = cls(
            name=data["name"],
            description=data["description"],
            trigger=data["trigger"],
            action=data["action"],
            category=data.get("category", "general"),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )
        skill.created_at = data.get("created_at", datetime.now().isoformat())
        skill.use_count = data.get("use_count", 0)
        skill.last_used = data.get("last_used")
        return skill

    def use(self):
        """Registra uso da skill."""
        self.use_count += 1
        self.last_used = datetime.now().isoformat()


class SkillSystem:
    """Gerencia todas as skills do sistema Saraswat."""

    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self._ensure_dirs()
        self._load_skills()

    def _ensure_dirs(self):
        SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    def _load_skills(self):
        """Carrega skills do índice."""
        if SKILLS_INDEX.exists():
            try:
                data = json.loads(SKILLS_INDEX.read_text(encoding="utf-8"))
                for name, skill_data in data.get("skills", {}).items():
                    self.skills[name] = Skill.from_dict(skill_data)
            except (json.JSONDecodeError, KeyError):
                pass

    def _save_skills(self):
        """Salva skills no índice."""
        data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "skills": {name: skill.to_dict() for name, skill in self.skills.items()},
        }
        SKILLS_INDEX.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def register(self, skill: Skill) -> bool:
        """Registra uma nova skill."""
        if skill.name in self.skills:
            return False  # Já existe
        self.skills[skill.name] = skill
        self._save_skills()
        return True

    def get(self, name: str) -> Optional[Skill]:
        """Retorna uma skill pelo nome."""
        return self.skills.get(name)

    def find_by_trigger(self, text: str) -> List[Skill]:
        """Encontra skills que correspondem ao texto."""
        matches = []
        text_lower = text.lower()
        for skill in self.skills.values():
            if not skill.enabled:
                continue
            # Check if trigger word is in text
            trigger_words = skill.trigger.lower().split(",")
            for word in trigger_words:
                if word.strip() in text_lower:
                    matches.append(skill)
                    break
        return matches

    def list_skills(self, category: Optional[str] = None) -> List[Skill]:
        """Lista skills, opcionalmente filtradas por categoria."""
        skills = list(self.skills.values())
        if category:
            skills = [s for s in skills if s.category == category]
        return sorted(skills, key=lambda s: s.use_count, reverse=True)

    def disable(self, name: str) -> bool:
        """Desativa uma skill."""
        if name in self.skills:
            self.skills[name].enabled = False
            self._save_skills()
            return True
        return False

    def enable(self, name: str) -> bool:
        """Ativa uma skill."""
        if name in self.skills:
            self.skills[name].enabled = True
            self._save_skills()
            return True
        return False

    def remove(self, name: str) -> bool:
        """Remove uma skill."""
        if name in self.skills:
            del self.skills[name]
            self._save_skills()
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas das skills."""
        total = len(self.skills)
        enabled = sum(1 for s in self.skills.values() if s.enabled)
        categories = {}
        for s in self.skills.values():
            categories[s.category] = categories.get(s.category, 0) + 1
        most_used = sorted(
            self.skills.values(), key=lambda s: s.use_count, reverse=True
        )[:5]

        return {
            "total": total,
            "enabled": enabled,
            "disabled": total - enabled,
            "categories": categories,
            "most_used": [(s.name, s.use_count) for s in most_used],
        }


def create_default_skills() -> List[Skill]:
    """Cria skills padrão do sistema."""
    return [
        Skill(
            name="system_check",
            description="Verifica saúde do sistema (disco, memória, ollama)",
            trigger="status,verificar,check,saúde,sistema",
            action="Run system health check: disk space, memory files integrity, ollama status. Report findings.",
            category="system",
        ),
        Skill(
            name="memory_search",
            description="Busca nas memórias do sistema",
            trigger="buscar,procurar,lembrar,memory,memória",
            action="Search memory files in D:\\.openclaude\\memory\\ for relevant information. Return snippets with file and line references.",
            category="memory",
        ),
        Skill(
            name="diary_entry",
            description="Adiciona entrada ao diário",
            trigger="diário,registrar,entry,acontecimento",
            action="Add a new entry to DIARY.md with timestamp and session context.",
            category="memory",
        ),
        Skill(
            name="evolution_check",
            description="Executa ciclo de evolução",
            trigger="evolução,evoluir,otimizar,cleanup,limpar",
            action="Run evolution daemon cycle: check disk, check memory files, check ollama, cleanup temp, record findings.",
            category="evolution",
        ),
        Skill(
            name="github_scan",
            description="Escaneia repositórios GitHub",
            trigger="github,repositório,repo,scan",
            action="Use GitHub API to scan repositories. List repos, check for updates, report findings.",
            category="github",
        ),
        Skill(
            name="learn",
            description="Registra um aprendizado",
            trigger="aprender,learning,descoberta,insight",
            action="Record a new learning in LEARNINGS.md with timestamp and source.",
            category="evolution",
        ),
        Skill(
            name="mistake_log",
            description="Registra um erro para não repetir",
            trigger="erro,mistake,falha,bug,problema",
            action="Record a mistake in MISTAKES.md with description and fix.",
            category="evolution",
        ),
    ]


# ── Singleton ──
_system: Optional[SkillSystem] = None


def get_system() -> SkillSystem:
    """Retorna instância singleton do SkillSystem."""
    global _system
    if _system is None:
        _system = SkillSystem()
        # Register defaults if empty
        if not _system.skills:
            for skill in create_default_skills():
                _system.register(skill)
    return _system


if __name__ == "__main__":
    ss = get_system()
    print("=== SKILL SYSTEM ===")
    print(f"Skills: {len(ss.skills)}")
    for skill in ss.list_skills():
        status = "✅" if skill.enabled else "❌"
        print(f"  {status} {skill.name} ({skill.category}) - {skill.description}")
    print(f"\nStats: {json.dumps(ss.get_stats(), indent=2)}")
