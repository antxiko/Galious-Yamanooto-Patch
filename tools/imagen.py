#!/usr/bin/env python3
"""Monta la imagen de 2 MB lista para grabar en un Yamanooto.

La imagen es el menu de nPackR con su directorio ya hecho para este juego
(menu/menu.bin, sin un byte del juego) y, desde 0x20000, el juego parcheado
por el script de packager/ a partir de la ROM de cada uno. Lo demas, 0xFF.
Vale para los cartuchos de 2 MB y de 8 MB: la de 8 MB que saca nPackR es
esta misma con 6 MB de 0xFF detras.

Lo que cambia de un juego a otro esta en tools/juego.py.

Uso: python tools/imagen.py <tu ROM> [salida]
"""
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))
import juego  # noqa: E402

TAM_IMAGEN = 0x200000
JUEGO_EN = 0x20000


def monta(rom_path):
    """Devuelve la imagen de 2 MB hecha desde la ROM de rom_path."""
    with tempfile.TemporaryDirectory() as tmp:
        parcheado = Path(tmp) / "parcheado.rom"
        r = subprocess.run([sys.executable, str(RAIZ / juego.PARCHEADOR),
                            str(rom_path), str(parcheado)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(r.stdout + r.stderr)
        datos = parcheado.read_bytes()
    if len(datos) != juego.TAM_PARCHEADO:
        raise SystemExit(f"el juego parcheado mide {len(datos)} bytes, "
                         f"no {juego.TAM_PARCHEADO}")
    menu = (RAIZ / "menu" / "menu.bin").read_bytes()
    assert len(menu) <= JUEGO_EN
    img = bytearray(b"\xff" * TAM_IMAGEN)
    img[:len(menu)] = menu
    img[JUEGO_EN:JUEGO_EN + len(datos)] = datos
    return bytes(img)


def main():
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    rom = Path(sys.argv[1])
    salida = Path(sys.argv[2]) if len(sys.argv) == 3 else RAIZ / juego.SALIDA
    sha = hashlib.sha256(rom.read_bytes()).hexdigest()
    if sha != juego.SHA256_ROM:
        print(f"aviso: {rom.name} no es el volcado conocido ({juego.SHA256_ROM[:16]}...);"
              " el parcheador comprueba cada sitio y se niega si no cuadra")
    img = monta(rom)
    salida.write_bytes(img)
    sha_img = hashlib.sha256(img).hexdigest()
    igual = " = la de referencia" if sha_img == juego.SHA256_IMAGEN else ""
    print(f"{salida} ({len(img)} bytes), sha256 {sha_img[:16]}...{igual}")


if __name__ == "__main__":
    main()
