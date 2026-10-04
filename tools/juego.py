"""Lo que distingue a este parche de los otros de la misma maquinaria."""
NOMBRE = "The Maze of Galious"
ROM = "galious.rom"                       # RC-749, Konami-4, 128 KB
TAM_ROM = 0x20000
SHA256_ROM = "420c42c18006eb5dbb25efa5b83e340d740824c15a714929a945c0db51f97280"
PARCHEADOR = "packager/galious_to_yamanooto.py"
TAM_PARCHEADO = 0x20000 + 0x2000         # + el driver como banco 0x10
FUENTES = ["galious_engine.asm", "galious_shim.asm", "galious_driver.asm"]
INCLUYE = {"galious_driver.asm": ["galious_engine.bin"]}
SALIDA = "galious_yamanooto.rom"
IPS = "ips/galious_yamanooto.ips"           # de la ROM a la imagen, publicado
SECTOR = 0x18 * 0x2000                   # el sector de 64 KB donde graba
TAM_IMAGEN = SECTOR + 0x10000           # 256 KB, para el offset 0 de la flash
SHA256_IMAGEN = "35626e09e20caf986b0cc05f20f166337d85018a766c0dc1ed750b198ee621b8"

# Los tramos que el parcheador declara (offset, largo): fuera de ellos, el
# juego parcheado es la ROM original byte a byte (tests/test_parche.py)
import sys as _s, pathlib as _p                        # noqa: E402
_s.path.insert(0, str(_p.Path(__file__).resolve().parent.parent / "packager"))
import galious_to_yamanooto as _q                      # noqa: E402
ZONAS = ([(off, len(old)) for _, off, old, _ in _q.SITES] + [(_q.SHIM_OFFSET, _q.SHIM_MAX)]
         + [(off + 2, 1) for off in _q.MAPPER_SITES])
