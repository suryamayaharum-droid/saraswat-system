#!/usr/bin/env python3
"""
Saraswat Disk Hunter v1.0
Encontra arquivos grandes no C: e move para D: ou deleta.
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

LOG_FILE = Path("D:/.openclaude/memory/architect/disk_hunter.log")
DUMP_DIR = Path("D:/disk_dump")

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def get_free_gb(drive="C:"):
    d = shutil.disk_usage(drive)
    return round(d.free / (1024**3), 2)

def find_big_files(min_mb=20):
    """Encontra arquivos grandes no C: excluindo diretorios do sistema."""
    skip = {
        "Windows", "Program Files", "Program Files (x86)", "ProgramData",
        "$Recycle.Bin", "System Volume Information", "Recovery",
    }
    big = []
    for dirpath, dirnames, filenames in os.walk("C:/"):
        # Skip system dirs
        parts = Path(dirpath).parts
        if any(s in parts for s in skip):
            dirnames.clear()
            continue
        for fn in filenames:
            fp = Path(dirpath) / fn
            try:
                size = fp.stat().st_size
                if size >= min_mb * 1024 * 1024:
                    big.append({"path": str(fp), "size_mb": round(size/1024**2, 1)})
            except:
                pass
    big.sort(key=lambda x: x["size_mb"], reverse=True)
    return big[:50]

def safe_move(src, dst_dir):
    """Move arquivo para dst_dir."""
    src = Path(src)
    dst_dir = Path(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    try:
        shutil.move(str(src), str(dst))
        return True
    except Exception as e:
        log(f"  MOVE ERROR: {e}")
        return False

def main():
    log("=== DISK HUNTER ===")
    free_before = get_free_gb("C:")
    log(f"C: Free before: {free_before}GB")

    # Find big files
    log("\n--- Scanning for large files ---")
    big = find_big_files(20)
    log(f"Found {len(big)} files > 20MB")
    for f in big[:20]:
        log(f"  {f['size_mb']}MB: {f['path']}")

    # Identify safe-to-move files
    safe_patterns = [
        ".msi", ".exe", ".zip", ".tar", ".gz", ".rar", ".7z",  # installers/archives
        ".iso", ".img",  # disk images
        ".mp4", ".avi", ".mkv", ".mov",  # videos
        ".mp3", ".wav", ".flac",  # audio
        ".pdf", ".docx", ".xlsx",  # documents
    ]

    skip_patterns = [
        "hiberfil", "pagefile", "swapfile",  # system files
        "ntuser", "usrclass",  # registry
    ]

    total_moved = 0
    total_files = 0

    for f in big:
        fp = f["path"]
        size = f["size_mb"]

        # Skip system files
        if any(s.lower() in fp.lower() for s in skip_patterns):
            log(f"  SKIP (system): {fp}")
            continue

        # Only move safe file types
        ext = Path(fp).suffix.lower()
        if ext not in safe_patterns:
            log(f"  SKIP (type): {fp}")
            continue

        # Move to D:/disk_dump
        if safe_move(fp, DUMP_DIR):
            log(f"  MOVED: {size}MB -> D:/disk_dump/{Path(fp).name}")
            total_moved += size
            total_files += 1
        else:
            log(f"  FAILED: {fp}")

    # Also check Downloads for big files
    log("\n--- Checking Downloads ---")
    downloads = Path(os.environ.get("USERPROFILE", "C:/Users/harum")) / "Downloads"
    if downloads.exists():
        dl_files = []
        for f in downloads.rglob("*"):
            try:
                if f.is_file() and f.stat().st_size >= 10 * 1024 * 1024:
                    dl_files.append({"path": str(f), "size_mb": round(f.stat().st_size/1024**2, 1)})
            except:
                pass
        dl_files.sort(key=lambda x: x["size_mb"], reverse=True)
        log(f"Downloads: {len(dl_files)} files > 10MB")
        for f in dl_files[:10]:
            log(f"  {f['size_mb']}MB: {f['path']}")

        # Move big downloads
        dl_moved = 0
        for f in dl_files:
            if safe_move(f["path"], DUMP_DIR / "downloads"):
                dl_moved += f["size_mb"]
                total_files += 1
        total_moved += dl_moved
        log(f"Moved from Downloads: {round(dl_moved, 1)}MB")

    # Check result
    free_after = get_free_gb("C:")
    log(f"\nC: Free after: {free_after}GB")
    log(f"Moved: {round(total_moved, 1)}MB in {total_files} files")
    log(f"Net gain: {round(free_after - free_before, 2)}GB")
    log(f"Dump dir: {DUMP_DIR}")
    log("=== DONE ===")

if __name__ == "__main__":
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    main()
