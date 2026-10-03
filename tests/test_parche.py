"""Lo que tiene que cumplir el parche, con la ROM y sin ella."""
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))
import juego  # noqa: E402
import imagen  # noqa: E402

ROM = RAIZ / juego.ROM


class Ensamblado(unittest.TestCase):
    """Los .bin que van en launcher/ son los que salen de sus .asm."""

    @unittest.skipUnless(shutil.which("pasmo"), "sin pasmo en el PATH")
    def test_bins(self):
        with tempfile.TemporaryDirectory() as tmp:
            for asm in juego.FUENTES:  # en orden: el motor va dentro del driver
                src = RAIZ / "launcher" / asm
                shutil.copy(src, tmp)
                for b in juego.INCLUYE.get(asm, ()):
                    shutil.copy(RAIZ / "launcher" / b, tmp)
                salida = Path(tmp) / src.with_suffix(".bin").name
                subprocess.run(["pasmo", "--bin", src.name, salida.name],
                               cwd=tmp, check=True, capture_output=True)
                self.assertEqual(salida.read_bytes(),
                                 src.with_suffix(".bin").read_bytes(), asm)


class Menu(unittest.TestCase):
    def test_cabe_antes_del_juego(self):
        menu = (RAIZ / "menu" / "menu.bin").read_bytes()
        self.assertLessEqual(len(menu), imagen.JUEGO_EN)
        self.assertNotEqual(menu[-1], 0xFF)

    @unittest.skipUnless(ROM.exists(), f"sin {juego.ROM}")
    def test_no_lleva_nada_del_juego(self):
        menu = (RAIZ / "menu" / "menu.bin").read_bytes()
        rom = ROM.read_bytes()
        trozos = {rom[i:i + 64] for i in range(0, len(rom), 64)
                  if len(set(rom[i:i + 64])) > 4}
        for i in range(0, len(menu) - 64, 16):
            self.assertNotIn(menu[i:i + 64], trozos, hex(i))


class Parcheador(unittest.TestCase):
    def test_rechaza_otra_rom(self):
        with tempfile.TemporaryDirectory() as tmp:
            falsa = Path(tmp) / "falsa.rom"
            falsa.write_bytes(bytes(juego.TAM_ROM))
            r = subprocess.run([sys.executable, str(RAIZ / juego.PARCHEADOR),
                                str(falsa), str(Path(tmp) / "x.rom")],
                               capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertFalse((Path(tmp) / "x.rom").exists())

    @unittest.skipUnless(ROM.exists(), f"sin {juego.ROM}")
    def test_fuera_de_lo_declarado_es_el_original(self):
        rom = ROM.read_bytes()
        img = imagen.monta(ROM)
        juego_p = img[imagen.JUEGO_EN:imagen.JUEGO_EN + juego.TAM_PARCHEADO]
        dentro = set()
        for off, n in juego.ZONAS:
            dentro.update(range(off, off + n))
        fuera = [i for i in range(len(rom)) if rom[i] != juego_p[i] and i not in dentro]
        self.assertEqual(fuera, [])
        driver = [b for b in juego.FUENTES if "driver" in b][0]
        self.assertEqual(juego_p[len(rom):],
                         (RAIZ / "launcher" / driver).with_suffix(".bin").read_bytes())

    @unittest.skipUnless(ROM.exists(), f"sin {juego.ROM}")
    def test_imagen_de_referencia(self):
        self.assertEqual(hashlib.sha256(ROM.read_bytes()).hexdigest(),
                         juego.SHA256_ROM)
        img = imagen.monta(ROM)
        self.assertEqual(len(img), imagen.TAM_IMAGEN)
        self.assertEqual(hashlib.sha256(img).hexdigest(), juego.SHA256_IMAGEN)


if __name__ == "__main__":
    unittest.main()
