#!/usr/bin/env python3
"""
Saraswat Cron Scheduler v1.0
Agendador de tarefas inspirado no hermes-agent.

Funciona como um daemon leve que verifica tarefas agendadas
e as executa no horário correto.

Jobs são salvos em JSON e persistidos entre sessões.
"""

import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

# Paths
MEMORY_DIR = Path("D:/.openclaude/memory")
CRON_FILE = MEMORY_DIR / "cron_jobs.json"
CRON_LOG = MEMORY_DIR / "cron.log"


class CronJob:
    """Uma tarefa agendada."""

    def __init__(
        self,
        name: str,
        schedule: str,  # "daily:09:00", "hourly", "every:3600", "once:2026-05-07T10:00:00"
        action: str,  # Descrição da ação a executar
        enabled: bool = True,
        last_run: Optional[str] = None,
        next_run: Optional[str] = None,
        run_count: int = 0,
    ):
        self.name = name
        self.schedule = schedule
        self.action = action
        self.enabled = enabled
        self.last_run = last_run
        self.next_run = next_run or self._calc_next_run()
        self.run_count = run_count

    def _calc_next_run(self) -> str:
        """Calcula próximo horário de execução."""
        now = datetime.now()
        try:
            if self.schedule == "hourly":
                return (now + timedelta(hours=1)).isoformat()
            elif self.schedule == "daily:09:00":
                target = now.replace(hour=9, minute=0, second=0, microsecond=0)
                if target <= now:
                    target += timedelta(days=1)
                return target.isoformat()
            elif self.schedule == "daily:21:00":
                target = now.replace(hour=21, minute=0, second=0, microsecond=0)
                if target <= now:
                    target += timedelta(days=1)
                return target.isoformat()
            elif self.schedule.startswith("every:"):
                seconds = int(self.schedule.split(":")[1])
                return (now + timedelta(seconds=seconds)).isoformat()
            elif self.schedule.startswith("once:"):
                return self.schedule.split(":", 1)[1]
            else:
                return (now + timedelta(hours=1)).isoformat()
        except Exception:
            return (now + timedelta(hours=1)).isoformat()

    def is_due(self) -> bool:
        """Verifica se a tarefa está pronta para executar."""
        if not self.enabled:
            return False
        if not self.next_run:
            return False
        try:
            next_dt = datetime.fromisoformat(self.next_run)
            return datetime.now() >= next_dt
        except Exception:
            return False

    def mark_run(self):
        """Marca que foi executada."""
        self.last_run = datetime.now().isoformat()
        self.run_count += 1
        self.next_run = self._calc_next_run()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "schedule": self.schedule,
            "action": self.action,
            "enabled": self.enabled,
            "last_run": self.last_run,
            "next_run": self.next_run,
            "run_count": self.run_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CronJob":
        return cls(
            name=data["name"],
            schedule=data["schedule"],
            action=data["action"],
            enabled=data.get("enabled", True),
            last_run=data.get("last_run"),
            next_run=data.get("next_run"),
            run_count=data.get("run_count", 0),
        )


class CronScheduler:
    """Agendador de tarefas do sistema Saraswat."""

    def __init__(self):
        self.jobs: Dict[str, CronJob] = {}
        self._load_jobs()

    def _load_jobs(self):
        """Carrega jobs do arquivo."""
        if CRON_FILE.exists():
            try:
                data = json.loads(CRON_FILE.read_text(encoding="utf-8"))
                for name, job_data in data.get("jobs", {}).items():
                    self.jobs[name] = CronJob.from_dict(job_data)
            except (json.JSONDecodeError, KeyError):
                pass

    def _save_jobs(self):
        """Salva jobs no arquivo."""
        data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "jobs": {name: job.to_dict() for name, job in self.jobs.items()},
        }
        CRON_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def add_job(self, job: CronJob) -> bool:
        """Adiciona um novo job."""
        if job.name in self.jobs:
            return False
        self.jobs[job.name] = job
        self._save_jobs()
        return True

    def remove_job(self, name: str) -> bool:
        """Remove um job."""
        if name in self.jobs:
            del self.jobs[name]
            self._save_jobs()
            return True
        return False

    def enable_job(self, name: str) -> bool:
        if name in self.jobs:
            self.jobs[name].enabled = True
            self._save_jobs()
            return True
        return False

    def disable_job(self, name: str) -> bool:
        if name in self.jobs:
            self.jobs[name].enabled = False
            self._save_jobs()
            return True
        return False

    def get_due_jobs(self) -> List[CronJob]:
        """Retorna jobs que estão prontos para executar."""
        return [job for job in self.jobs.values() if job.is_due()]

    def list_jobs(self) -> List[CronJob]:
        """Lista todos os jobs."""
        return sorted(self.jobs.values(), key=lambda j: j.next_run or "")

    def log(self, message: str):
        """Log com timestamp."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {message}"
        with open(CRON_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def create_default_jobs() -> List[CronJob]:
    """Cria jobs padrão do sistema."""
    return [
        CronJob(
            name="system_health_check",
            schedule="every:3600",  # A cada hora
            action="Run evolution daemon cycle: check disk, memory files, ollama status, cleanup temp.",
        ),
        CronJob(
            name="daily_reflection",
            schedule="daily:21:00",  # Todo dia às 21h
            action="Reflect on the day. What was learned? What mistakes were made? Update DIARY.md, LEARNINGS.md, MISTAKES.md accordingly.",
        ),
        CronJob(
            name="github_sync",
            schedule="daily:09:00",  # Todo dia às 9h
            action="Check GitHub repos for updates. Pull latest changes from key repos. Report any significant changes.",
        ),
    ]


# ── Singleton ──
_scheduler: Optional[CronScheduler] = None


def get_scheduler() -> CronScheduler:
    """Retorna instância singleton do CronScheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = CronScheduler()
        # Register defaults if empty
        if not _scheduler.jobs:
            for job in create_default_jobs():
                _scheduler.add_job(job)
    return _scheduler


if __name__ == "__main__":
    cs = get_scheduler()
    print("=== CRON SCHEDULER ===")
    print(f"Jobs: {len(cs.jobs)}")
    for job in cs.list_jobs():
        status = "✅" if job.enabled else "❌"
        due = "🔴 DUE" if job.is_due() else f"⏰ {job.next_run[:16] if job.next_run else '?'}"
        print(f"  {status} {job.name} | {job.schedule} | {due} | runs: {job.run_count}")
    print(f"\nDue now: {len(cs.get_due_jobs())}")
