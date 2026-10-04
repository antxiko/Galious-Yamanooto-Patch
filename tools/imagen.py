#!/usr/bin/env python3
"""Monta la imagen para grabar en un Yamanooto, sin menu: el juego arranca
solo.

La imagen es el juego parcheado por el script de packager/ a partir de la
ROM de cada uno, en el offset 0 de la flash, y detras 0xFF hasta cubrir el
sector de 64 KB donde graba (en blanco). El juego va en el modo con el que
arranca el Yamanooto (Konami SCC), asi que no hace falta nada mas.

Lo que cambia de un juego a otro esta en tools/juego.py; la segunda edicion,
The Maze of Galious Enhanced (bladeba v1.04, MSX2), en tools/juego_enhanced.py.
Se elige por el tamano de la ROM: 128 KB el original, 512 KB el Enhanced (el
IPS ya aplicado).

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
import juego_enhanced  # noqa: E402

EDICIONES = (juego, juego_enhanced)


def edicion(rom_path):
    """El juego.py que toca a la ROM de rom_path, por su tamano."""
    tam = Path(rom_path).stat().st_size
    for j in EDICIONES:
        if tam == j.TAM_ROM:
            return j
    raise SystemExit(f"{Path(rom_path).name}: {tam} bytes; se espera "
                     + " o ".join(f"{j.TAM_ROM} ({j.NOMBRE})" for j in EDICIONES))


def monta(rom_path, juego=None):
    """Devuelve la imagen hecha desde la ROM de rom_path."""
    juego = juego or edicion(rom_path)
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
    assert juego.SECTOR + 0x10000 == juego.TAM_IMAGEN > len(datos)
    return datos + b"\xff" * (juego.TAM_IMAGEN - len(datos))


def main():
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    rom = Path(sys.argv[1])
    juego = edicion(rom)
    salida = Path(sys.argv[2]) if len(sys.argv) == 3 else RAIZ / juego.SALIDA
    sha = hashlib.sha256(rom.read_bytes()).hexdigest()
    if sha != juego.SHA256_ROM:
        print(f"aviso: {rom.name} no es el volcado conocido ({juego.SHA256_ROM[:16]}...);"
              " el parcheador comprueba cada sitio y se niega si no cuadra")
    img = monta(rom, juego)
    salida.write_bytes(img)
    sha_img = hashlib.sha256(img).hexdigest()
    igual = " = la de referencia" if sha_img == juego.SHA256_IMAGEN else ""
    print(f"{salida} ({len(img)} bytes), sha256 {sha_img[:16]}...{igual}")


if __name__ == "__main__":
    main()
