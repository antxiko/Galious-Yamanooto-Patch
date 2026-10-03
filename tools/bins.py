#!/usr/bin/env python3
"""Ensambla con pasmo los .asm de launcher/ (los de tools/juego.py, en orden:
el motor va dentro del driver) y comprueba que el driver mide 8 KB."""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))
import juego  # noqa: E402

for asm in juego.FUENTES:
    b = Path(asm).with_suffix(".bin").name
    subprocess.run(["pasmo", "--bin", asm, b], cwd=RAIZ / "launcher", check=True)
    tam = (RAIZ / "launcher" / b).stat().st_size
    if tam == 0 or ("driver" in asm and tam != 0x2000):
        raise SystemExit(f"{b}: {tam} bytes")
    print(f"{b}: {tam} bytes")
