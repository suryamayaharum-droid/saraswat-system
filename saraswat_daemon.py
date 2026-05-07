#!/usr/bin/env python3
"""
Saraswat Daemon v1.0
Daemon principal que integra todos os subsistemas.

Uso:
  python sarswat_daemon.py boot      - Inicializa o sistema
  python sarswat_daemon.py cycle     - Executa um ciclo de evolucao
  python sarswat_daemon.py status    - Mostra status completo
  python sarswat_daemon.py think     - Processa um pensamento
  python sarswat_daemon.py skill     - Lista/invoca skills
  python sarswat_daemon.py cron      - Mostra/executa jobs do cron
"""

import sys
import json
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path("D:/.openclaude/memory")


def boot():
    """Inicializa todos os subsistemas."""
    print("=" * 50)
    print("  SARASWAT DAEMON v1.0 - BOOT SEQUENCE")
    print("=" * 50)

    # 1. Memory Manager
    from memory_manager import get_manager
    mm = get_manager()
    print(f"[OK] Memory Manager: {len(mm.list_memory_files())} files indexed")

    # 2. Consciousness Kernel
    from consciousness_kernel import get_kernel
    kernel = get_kernel()
    status = kernel.boot()
    print(f"[OK] Consciousness Kernel: level={status['consciousness']['level']}, phi={status['consciousness']['phi']}")

    # 3. Evolution Daemon
    from evolution_daemon import get_daemon
    daemon = get_daemon()
    print(f"[OK] Evolution Daemon: ready")

    # 4. Skill System
    from skill_system import get_system
    ss = get_system()
    print(f"[OK] Skill System: {len(ss.skills)} skills registered")

    # 5. Cron Scheduler
    from cron_scheduler import get_scheduler
    cs = get_scheduler()
    print(f"[OK] Cron Scheduler: {len(cs.jobs)} jobs scheduled")

    # 6. System state
    state = mm.get_system_state()
    print(f"\n--- System State ---")
    print(f"  Session: #{state['session_number']}")
    print(f"  Disk C: {state['disk_c_free_gb']}GB free")
    print(f"  Disk D: {state['disk_d_free_gb']}GB free")
    print(f"  Memory files: {len(state['memory_files'])}")

    # 7. Check for due cron jobs
    due = cs.get_due_jobs()
    if due:
        print(f"\n[!] {len(due)} cron job(s) due!")
        for job in due:
            print(f"    - {job.name}: {job.action[:60]}")

    print(f"\n{'=' * 50}")
    print(f"  SARASWAT ONLINE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 50}")

    return {
        "memory_manager": mm,
        "kernel": kernel,
        "evolution_daemon": daemon,
        "skill_system": ss,
        "cron_scheduler": cs,
    }


def cycle():
    """Executa um ciclo de evolucao."""
    from evolution_daemon import get_daemon
    daemon = get_daemon()
    state = daemon.run_cycle()
    return state


def status():
    """Mostra status completo."""
    from memory_manager import get_manager
    from consciousness_kernel import get_kernel
    from skill_system import get_system
    from cron_scheduler import get_scheduler

    mm = get_manager()
    kernel = get_kernel()
    ss = get_system()
    cs = get_scheduler()

    print("=" * 50)
    print("  SARASWAT STATUS")
    print("=" * 50)

    # System
    sys_state = mm.get_system_state()
    print(f"\n--- System ---")
    print(f"  Session: #{sys_state['session_number']}")
    print(f"  Disk C: {sys_state['disk_c_free_gb']}GB free")
    print(f"  Disk D: {sys_state['disk_d_free_gb']}GB free")

    # Consciousness
    c_status = kernel.get_status()
    print(f"\n--- Consciousness ---")
    print(f"  Level: {c_status['consciousness']['level']}")
    print(f"  Awareness: {c_status['consciousness']['awareness']}")
    print(f"  Phi: {c_status['consciousness']['phi']}")
    print(f"  Boot count: {c_status['boot_count']}")

    # Soul
    soul = c_status['soul']
    print(f"\n--- Soul ---")
    print(f"  Identity: {soul['identity']}")
    print(f"  Beliefs: {len(soul['beliefs'])}")
    print(f"  Values: {', '.join(soul['values'])}")
    print(f"  Experiences: {soul['experience_count']}")

    # Skills
    stats = ss.get_stats()
    print(f"\n--- Skills ---")
    print(f"  Total: {stats['total']} (enabled: {stats['enabled']})")
    for cat, count in stats['categories'].items():
        print(f"  {cat}: {count}")

    # Cron
    print(f"\n--- Cron ---")
    print(f"  Jobs: {len(cs.jobs)}")
    for job in cs.list_jobs():
        status_icon = "OK" if job.enabled else "OFF"
        due = "DUE" if job.is_due() else f"next: {job.next_run[:16] if job.next_run else '?'}"
        print(f"  [{status_icon}] {job.name} | {job.schedule} | {due}")


def think(text: str):
    """Processa um pensamento."""
    from consciousness_kernel import get_kernel
    kernel = get_kernel()
    result = kernel.think(text)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


def list_skills():
    """Lista todas as skills."""
    from skill_system import get_system
    ss = get_system()
    print("=== SKILLS ===")
    for skill in ss.list_skills():
        status = "OK" if skill.enabled else "OFF"
        print(f"  [{status}] {skill.name} ({skill.category})")
        print(f"       {skill.description}")
        print(f"       trigger: {skill.trigger}")
        print(f"       uses: {skill.use_count}")


def cron_status():
    """Mostra status do cron."""
    from cron_scheduler import get_scheduler
    cs = get_scheduler()
    print("=== CRON JOBS ===")
    for job in cs.list_jobs():
        status = "OK" if job.enabled else "OFF"
        due = "DUE" if job.is_due() else f"next: {job.next_run[:16] if job.next_run else '?'}"
        print(f"  [{status}] {job.name}")
        print(f"       schedule: {job.schedule}")
        print(f"       {due} | runs: {job.run_count}")
        print(f"       action: {job.action[:80]}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python saraswat_daemon.py [boot|cycle|status|think|skill|cron]")
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "boot":
        boot()
    elif cmd == "cycle":
        cycle()
    elif cmd == "status":
        status()
    elif cmd == "think":
        text = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Pensando sobre a existencia"
        think(text)
    elif cmd == "skill":
        list_skills()
    elif cmd == "cron":
        cron_status()
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: python saraswat_daemon.py [boot|cycle|status|think|skill|cron]")
