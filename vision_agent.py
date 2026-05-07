#!/usr/bin/env python3
"""
Saraswat Vision Agent v1.0
Agente de visao e automacao inspirado no Jarvis.

Capacidades:
  - Screenshot da tela
  - OCR basico (reconhecimento de texto)
  - Deteccao de janelas ativas
  - Automatizacao de mouse/teclado (opcional, requer pyautogui)

Dependencias opcionais:
  pip install pyautogui pillow pygetwindow
"""

import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

MEMORY_DIR = Path("D:/.openclaude/memory")
SCREENSHOT_DIR = Path("D:/.openclaude/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


class VisionAgent:
    """Agente de visao e automacao do sistema Saraswat."""

    def __init__(self):
        self.has_pyautogui = False
        self.has_pillow = False
        self._check_deps()

    def _check_deps(self):
        """Verifica dependencias disponiveis."""
        try:
            import pyautogui
            self.has_pyautogui = True
        except ImportError:
            pass
        try:
            from PIL import Image
            self.has_pillow = True
        except ImportError:
            pass

    def get_screen_info(self) -> Dict[str, Any]:
        """Obtem informacoes da tela."""
        info = {
            "timestamp": datetime.now().isoformat(),
            "has_pyautogui": self.has_pyautogui,
            "has_pillow": self.has_pillow,
        }

        if self.has_pyautogui:
            import pyautogui
            info["screen_size"] = {"width": pyautogui.size().width, "height": pyautogui.size().height}
            info["mouse_position"] = {"x": pyautogui.position().x, "y": pyautogui.position().y}

        return info

    def list_windows(self) -> List[Dict[str, str]]:
        """Lista janelas ativas."""
        windows = []
        try:
            import pygetwindow as gw
            for w in gw.getAllWindows():
                if w.title and w.visible:
                    windows.append({
                        "title": w.title[:80],
                        "left": w.left,
                        "top": w.top,
                        "width": w.width,
                        "height": w.height,
                        "active": w.isActive,
                    })
        except ImportError:
            # Fallback via PowerShell
            try:
                result = subprocess.run(
                    ["powershell", "-Command",
                     "Get-Process | Where-Object {$_.MainWindowTitle} | Select-Object ProcessName, MainWindowTitle | ConvertTo-Json"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    procs = json.loads(result.stdout) if result.stdout.strip().startswith("[") else [json.loads(result.stdout)]
                    for p in procs:
                        windows.append({
                            "title": p.get("MainWindowTitle", "")[:80],
                            "process": p.get("ProcessName", ""),
                            "active": False,
                        })
            except Exception:
                pass

        return windows

    def screenshot(self, filename: str = None) -> Optional[str]:
        """Tira screenshot da tela."""
        if not self.has_pyautogui:
            return None

        import pyautogui
        if not filename:
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = SCREENSHOT_DIR / filename

        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(str(filepath))
            return str(filepath)
        except Exception as e:
            return f"Error: {e}"

    def get_active_window(self) -> Optional[Dict[str, Any]]:
        """Obtem janela ativa."""
        try:
            import pygetwindow as gw
            active = gw.getActiveWindow()
            if active:
                return {
                    "title": active.title[:80],
                    "left": active.left,
                    "top": active.top,
                    "width": active.width,
                    "height": active.height,
                }
        except ImportError:
            pass
        return None

    def mouse_move(self, x: int, y: int, duration: float = 0.25):
        """Move o mouse para uma posicao."""
        if not self.has_pyautogui:
            return "pyautogui not installed"
        import pyautogui
        pyautogui.moveTo(x, y, duration=duration)
        return f"Moved to ({x}, {y})"

    def mouse_click(self, x: int = None, y: int = None):
        """Clica na posicao atual ou especificada."""
        if not self.has_pyautogui:
            return "pyautogui not installed"
        import pyautogui
        if x is not None and y is not None:
            pyautogui.click(x, y)
        else:
            pyautogui.click()
        return f"Clicked at ({x or 'current'}, {y or 'current'})"

    def type_text(self, text: str, interval: float = 0.05):
        """Digita texto."""
        if not self.has_pyautogui:
            return "pyautogui not installed"
        import pyautogui
        pyautogui.typewrite(text, interval=interval)
        return f"Typed: {text[:50]}"

    def install_deps(self) -> str:
        """Instala dependencias necessarias."""
        try:
            subprocess.run(
                ["py", "-3.14", "-m", "pip", "install", "pyautogui", "pillow", "pygetwindow"],
                capture_output=True, text=True, timeout=60
            )
            self._check_deps()
            return f"Installed. pyautogui={self.has_pyautogui}, pillow={self.has_pillow}"
        except Exception as e:
            return f"Install failed: {e}"


_vision: Optional[VisionAgent] = None


def get_vision() -> VisionAgent:
    global _vision
    if _vision is None:
        _vision = VisionAgent()
    return _vision


if __name__ == "__main__":
    v = get_vision()
    print("=== VISION AGENT ===")
    print(json.dumps(v.get_screen_info(), indent=2))

    windows = v.list_windows()
    print(f"\nActive windows: {len(windows)}")
    for w in windows[:5]:
        print(f"  - {w['title']}")

    if v.has_pyautogui:
        print("\nPyAutoGUI available - full automation ready")
    else:
        print("\nPyAutoGUI not installed. Run: pip install pyautogui pillow pygetwindow")
