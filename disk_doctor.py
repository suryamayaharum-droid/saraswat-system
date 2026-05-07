#!/usr/bin/env python3
"""
Saraswat Disk Doctor v1.0
Encontra e limpa espaco no disco C de forma segura.
Usa apenas Python stdlib.
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

LOG_FILE = Path("D:/.openclaude/memory/architect/disk_doctor.log")
REPORT_FILE = Path("D:/.openclaude/memory/architect/disk_doctor.json")

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def get_free_gb(drive="C:"):
    d = shutil.disk_usage(drive)
    return round(d.free / (1024**3), 2)

def find_large_files(root, min_mb=50, max_depth=4):
    """Encontra arquivos maiores que min_mb."""
    large = []
    root = Path(root)
    for i, (dirpath, dirnames, filenames) in enumerate(os.walk(root)):
        depth = len(Path(dirpath).relative_to(root).parts)
        if depth > max_depth:
            dirnames.clear()
            continue
        for fn in filenames:
            fp = Path(dirpath) / fn
            try:
                size = fp.stat().st_size
                if size >= min_mb * 1024 * 1024:
                    large.append({"path": str(fp), "size_mb": round(size/1024**2, 1)})
            except (PermissionError, OSError):
                pass
    large.sort(key=lambda x: x["size_mb"], reverse=True)
    return large[:30]

def find_temp_dirs():
    """Encontra diretorios temporarios que podem ser limpos."""
    candidates = [
        Path(os.environ.get("TEMP", "C:/Windows/Temp")),
        Path("C:/Windows/Temp"),
        Path("C:/Windows/SoftwareDistribution/Download"),
        Path("C:/Windows/Prefetch"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Temp",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/User Data/Default/Cache",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/User Data/Default/Code Cache",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Edge/User Data/Default/Cache",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Edge/User Data/Default/Code Cache",
        Path(os.environ.get("LOCALAPPDATA", "")) / "npm-cache",
        Path(os.environ.get("LOCALAPPDATA", "")) / "pip/cache",
    ]
    results = []
    for p in candidates:
        if p.exists():
            total = 0
            count = 0
            for f in p.rglob("*"):
                try:
                    if f.is_file():
                        total += f.stat().st_size
                        count += 1
                except:
                    pass
            if total > 0:
                results.append({"path": str(p), "size_mb": round(total/1024**2, 1), "files": count})
    results.sort(key=lambda x: x["size_mb"], reverse=True)
    return results

def safe_delete_dir(path, dry_run=True):
    """Remove arquivos de um diretorio com seguranca."""
    p = Path(path)
    if not p.exists():
        return 0
    freed = 0
    count = 0
    for f in p.rglob("*"):
        try:
            if f.is_file():
                size = f.stat().st_size
                if not dry_run:
                    f.unlink()
                freed += size
                count += 1
        except:
            pass
    return freed, count

def main():
    log("=== DISK DOCTOR ===")

    free_before = get_free_gb("C:")
    log(f"C: Free before: {free_before}GB")

    if free_before >= 1.0:
        log("Disk C OK - no cleanup needed")
        return

    log("Disk C below 1GB - starting cleanup...")

    # 1. Find temp dirs
    log("\n--- Temp directories ---")
    temps = find_temp_dirs()
    total_temp = 0
    for t in temps:
        log(f"  {t['path']}: {t['size_mb']}MB ({t['files']} files)")
        total_temp += t["size_mb"]
    log(f"Total temp: {total_temp}MB")

    # 2. Clean temp dirs
    log("\n--- Cleaning ---")
    total_freed = 0
    for t in temps:
        if t["size_mb"] < 1:
            continue
        path = t["path"]
        # Skip critical dirs
        critical = ["SoftwareDistribution", "Prefetch"]
        if any(c in path for c in critical):
            log(f"  SKIP (critical): {path}")
            continue
        try:
            freed, count = safe_delete_dir(path, dry_run=False)
            freed_mb = round(freed/1024**2, 1)
            log(f"  CLEANED: {path} -> {freed_mb}MB ({count} files)")
            total_freed += freed_mb
        except Exception as e:
            log(f"  ERROR: {path} -> {e}")

    # 3. Run Windows Disk Cleanup via cleanmgr
    log("\n--- Windows temp cleanup ---")
    try:
        os.popen("cleanmgr /sagerun:1").read()
        log("  cleanmgr triggered")
    except:
        log("  cleanmgr not available")

    # 4. Clear pip cache
    log("\n--- Pip cache ---")
    try:
        result = os.popen("pip cache purge 2>&1").read()
        log(f"  pip cache: {result.strip()}")
    except:
        pass

    # 5. Clear npm cache
    log("\n--- NPM cache ---")
    try:
        result = os.popen("npm cache clean --force 2>&1").read()
        log(f"  npm cache: {result.strip()}")
    except:
        pass

    # 6. Check result
    free_after = get_free_gb("C:")
    log(f"\nC: Free after: {free_after}GB")
    log(f"Freed: {round(free_after - free_before, 2)}GB")

    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "free_before_gb": free_before,
        "free_after_gb": free_after,
        "freed_mb": total_freed,
        "temp_dirs": temps,
    }
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(json.dumps(report, indent=2, encoding="utf-8"), encoding="utf-8")
    log(f"\nReport saved: {REPORT_FILE}")
    log("=== DONE ===")

if __name__ == "__main__":
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    main()
