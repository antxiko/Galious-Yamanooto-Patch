#!/usr/bin/env python3
"""Los IPS del parche: de tu ROM a la imagen para el Yamanooto, sin Python.

Cada IPS lleva solo lo que cambia (los sitios, el shim, el driver y el sector
en blanco), nada del juego: se aplica con cualquier herramienta de IPS (Lunar
IPS, Floating IPS, la web de RomPatcher.js...) a la ROM de cada uno y sale la
misma imagen que con tools/imagen.py.

    python tools/ips.py                 rehace ips/*.ips desde las ROMs de la raiz
    python tools/ips.py aplica <ips> <rom> <salida>
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))
import imagen  # noqa: E402

MAX_REG = 0xFFFF
EOF_OFF = 0x454F46            # "EOF": un registro no puede empezar ahi


def _registros(off, tramo):
    """Un tramo a escribir, en registros: RLE para lo repetido, literal el resto."""
    out = bytearray()
    i = 0
    while i < len(tramo):
        j = i
        while j < len(tramo) and tramo[j] == tramo[i] and j - i < MAX_REG:
            j += 1
        if j - i >= 16:                                  # repetido: RLE
            assert off + i != EOF_OFF
            out += (off + i).to_bytes(3, "big") + bytes(2) + (j - i).to_bytes(2, "big") + tramo[i:i + 1]
            i = j
            continue
        k = i                                            # literal hasta el proximo repetido
        while k < len(tramo) and k - i < MAX_REG:
            if k + 16 <= len(tramo) and len(set(tramo[k:k + 16])) == 1:
                break
            k += 1
        k = max(k, i + 1)
        assert off + i != EOF_OFF
        out += (off + i).to_bytes(3, "big") + (k - i).to_bytes(2, "big") + tramo[i:k]
        i = k
    return out


def hace(rom: bytes, img: bytes) -> bytes:
    """El IPS que lleva rom a img (img no mas corta que rom). Lo que crece
    se escribe entero (aunque sea 0xFF): un IPS no sabe rellenar."""
    assert len(img) >= len(rom) and len(img) < 0x1000000
    out = bytearray(b"PATCH")
    i = 0
    while i < len(img):
        if i < len(rom) and img[i] == rom[i]:
            i += 1
            continue
        j = i
        while j < len(img) and (j >= len(rom) or img[j] != rom[j]):
            j += 1
        out += _registros(i, img[i:j])
        i = j
    out += b"EOF"
    return bytes(out)


def aplica(ips: bytes, rom: bytes) -> bytes:
    if ips[:5] != b"PATCH":
        raise SystemExit("no es un IPS")
    d = bytearray(rom)
    i = 5
    while ips[i:i + 3] != b"EOF":
        off = int.from_bytes(ips[i:i + 3], "big")
        n = int.from_bytes(ips[i + 3:i + 5], "big")
        i += 5
        if n == 0:
            n = int.from_bytes(ips[i:i + 2], "big")
            datos = ips[i + 2:i + 3] * n
            i += 3
        else:
            datos = ips[i:i + n]
            i += n
        if len(d) < off + n:
            d.extend(b"\x00" * (off + n - len(d)))
        d[off:off + n] = datos
    return bytes(d)


def main():
    if len(sys.argv) == 5 and sys.argv[1] == "aplica":
        ips, rom, salida = (Path(a) for a in sys.argv[2:])
        salida.write_bytes(aplica(ips.read_bytes(), rom.read_bytes()))
        print(f"{salida}")
        return
    if len(sys.argv) != 1:
        raise SystemExit(__doc__)
    (RAIZ / "ips").mkdir(exist_ok=True)
    for j in imagen.EDICIONES:
        rom_path = RAIZ / j.ROM
        if not rom_path.exists():
            print(f"sin {j.ROM}: no rehago {j.IPS}")
            continue
        rom = rom_path.read_bytes()
        ips = hace(rom, imagen.monta(rom_path, j))
        assert aplica(ips, rom) == imagen.monta(rom_path, j)
        (RAIZ / j.IPS).write_bytes(ips)
        print(f"{j.IPS}: {len(ips)} bytes")


if __name__ == "__main__":
    main()
