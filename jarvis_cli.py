#!/usr/bin/env python3
"""
J.A.R.V.I.S. Production CLI Executable
Auto-detects and activates local .venv to guarantee Apple MLX and all libraries load cleanly.
"""
import os
import sys

# ── 0. Virtual Environment Self-Bootstrap ──
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
_VENV_PYTHON = os.path.join(_PROJECT_DIR, ".venv", "bin", "python")
if not getattr(sys, 'frozen', False) and os.path.exists(_VENV_PYTHON) and os.path.realpath(sys.executable) != os.path.realpath(_VENV_PYTHON):
    try:
        os.execv(_VENV_PYTHON, [_VENV_PYTHON] + sys.argv)
    except Exception:
        pass

if __name__ == "__main__":
    from interfaces.cli import run_cli
    run_cli()
