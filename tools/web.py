#!/usr/bin/env python3
"""La web (GitHub Pages, main:/docs): el README en ingles en docs/ y el
castellano en docs/es/, una pagina por idioma, con el estilo de la serie.
El enlace de idioma del README sobra: la pagina lleva su selector."""
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))
import md2html  # noqa: E402

for readme, dest, idioma in (("README.md", "docs", "en"), ("README.es.md", "docs/es", "es")):
    texto = (RAIZ / readme).read_text(encoding="utf-8")
    texto = re.sub(r"^\*\[(English|Español)\]\(README(\.es)?\.md\)\*\n\n", "", texto, flags=re.M)
    (RAIZ / dest).mkdir(parents=True, exist_ok=True)
    (RAIZ / dest / "index.md").write_text(texto, encoding="utf-8")
    md2html.main(str(RAIZ / dest), idioma)
subprocess.run([sys.executable, str(RAIZ / "tools" / "check_enlaces.py"), str(RAIZ / "docs")], check=True)
