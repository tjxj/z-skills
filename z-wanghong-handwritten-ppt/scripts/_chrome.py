"""Chrome / Edge 无头调用的共用工具（macOS、Windows、Linux）。"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _candidates() -> list[str]:
    env = os.environ.get("WH_CHROME") or os.environ.get("CHROME_PATH")
    out: list[str] = [env] if env else []
    if sys.platform == "darwin":
        out += [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            str(Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ]
    elif os.name == "nt":
        roots = [os.environ.get(k) for k in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")]
        for root in filter(None, roots):
            out += [
                str(Path(root) / "Google/Chrome/Application/chrome.exe"),
                str(Path(root) / "Microsoft/Edge/Application/msedge.exe"),
                str(Path(root) / "Chromium/Application/chrome.exe"),
            ]
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge", "microsoft-edge"):
        found = shutil.which(name)
        if found:
            out.append(found)
    return out


def find_chrome(explicit: str | None = None) -> str | None:
    for cand in ([explicit] if explicit else []) + _candidates():
        if cand and Path(cand).is_file():
            return cand
    return None


def file_url(path: Path, query: str = "", fragment: str = "") -> str:
    url = path.resolve().as_uri()
    if query:
        url += "?" + query
    if fragment:
        url += "#" + fragment
    return url


def run_chrome(chrome: str, url: str, extra: list[str], *, width: int = 1920, height: int = 1080,
               scale: float = 1, budget_ms: int = 12000, timeout: int = 120,
               capture: bool = False) -> subprocess.CompletedProcess:
    """每次调用使用独立的临时用户目录，可并行运行。"""
    with tempfile.TemporaryDirectory(prefix="wh-chrome-") as profile:
        cmd = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--mute-audio",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--allow-file-access-from-files",
            "--run-all-compositor-stages-before-draw",
            f"--user-data-dir={profile}",
            f"--window-size={width},{height}",
            f"--force-device-scale-factor={scale:g}",
            f"--virtual-time-budget={budget_ms}",
            *extra,
            url,
        ]
        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )


def png_size(path: Path) -> tuple[int, int] | None:
    try:
        head = path.read_bytes()[:24]
    except OSError:
        return None
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")
