"""La segunda edicion: The Maze of Galious Enhanced (bladeba v1.04, MSX2)."""
NOMBRE = "The Maze of Galious Enhanced"
ROM = "galious_enhanced.rom"              # el IPS v1.04 aplicado a RC-749, KonamiSCC
TAM_ROM = 0x80000
SHA256_ROM = "cdeaa916d198a3ca9891076eb79e05709876fa7ce18dcd929e76f1cf25403f53"
PARCHEADOR = "packager/enhanced_to_yamanooto.py"
TAM_PARCHEADO = 0x80000                  # no crece: el driver va en su banco 0x0C
FUENTES = ["enhanced_engine.asm", "enhanced_shim.asm", "enhanced_driver.asm"]
INCLUYE = {"enhanced_driver.asm": ["enhanced_engine.bin"]}
SALIDA = "galious_enhanced_yamanooto.rom"
IPS = "ips/galious_enhanced_yamanooto.ips"           # de la ROM a la imagen, publicado
SECTOR = 0x40 * 0x2000                   # el sector de 64 KB donde graba
TAM_IMAGEN = SECTOR + 0x10000           # 576 KB, para el offset 0 de la flash
SHA256_IMAGEN = "37984837e7af538cff9a901ffc60553d94edabe2e57ebef0b9918eb099738213"

# Los tramos que el parcheador declara (offset, largo): fuera de ellos, el
# juego parcheado es la ROM original byte a byte (tests/test_parche.py)
import sys as _s, pathlib as _p                        # noqa: E402
_s.path.insert(0, str(_p.Path(__file__).resolve().parent.parent / "packager"))
import enhanced_to_yamanooto as _q                     # noqa: E402
DRIVER_EN = _q.DRIVER_OFFSET                           # dentro del juego
ZONAS = ([(off, len(old)) for _, off, old, _ in _q.SITES] + [(_q.SHIM_OFFSET, _q.SHIM_MAX)]
         + [(_q.DRIVER_OFFSET, 0x2000)])
