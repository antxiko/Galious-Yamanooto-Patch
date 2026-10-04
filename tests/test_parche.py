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
import juego_enhanced  # noqa: E402
import imagen  # noqa: E402
import ips  # noqa: E402


class Ensamblado:
    """Los .bin que van en launcher/ son los que salen de sus .asm."""
    juego = None

    def test_bins(self):
        juego = self.juego
        self.assertTrue(shutil.which("pasmo"), "hace falta pasmo en el PATH")
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


class Parcheador:
    juego = None

    def rom(self):
        rom = RAIZ / self.juego.ROM
        if not rom.exists():
            self.skipTest(f"sin {self.juego.ROM}")
        return rom

    def test_rechaza_otra_rom(self):
        juego = self.juego
        with tempfile.TemporaryDirectory() as tmp:
            falsa = Path(tmp) / "falsa.rom"
            falsa.write_bytes(bytes(juego.TAM_ROM))
            r = subprocess.run([sys.executable, str(RAIZ / juego.PARCHEADOR),
                                str(falsa), str(Path(tmp) / "x.rom")],
                               capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertFalse((Path(tmp) / "x.rom").exists())

    def test_fuera_de_lo_declarado_es_el_original(self):
        juego, ROM = self.juego, self.rom()
        rom = ROM.read_bytes()
        juego_p = imagen.monta(ROM, juego)[:juego.TAM_PARCHEADO]
        dentro = set()
        for off, n in juego.ZONAS:
            dentro.update(range(off, off + n))
        fuera = [i for i in range(len(rom)) if rom[i] != juego_p[i] and i not in dentro]
        self.assertEqual(fuera, [])
        driver = [b for b in juego.FUENTES if "driver" in b][0]
        en = getattr(juego, "DRIVER_EN", len(rom))   # detras del juego o dentro
        self.assertEqual(juego_p[en:en + 0x2000],
                         (RAIZ / "launcher" / driver).with_suffix(".bin").read_bytes())

    def test_imagen_de_referencia(self):
        juego, ROM = self.juego, self.rom()
        self.assertEqual(hashlib.sha256(ROM.read_bytes()).hexdigest(),
                         juego.SHA256_ROM)
        img = imagen.monta(ROM, juego)
        self.assertEqual(len(img), juego.TAM_IMAGEN)
        self.assertEqual(set(img[juego.SECTOR:]), {0xFF})   # el sector, en blanco
        self.assertEqual(hashlib.sha256(img).hexdigest(), juego.SHA256_IMAGEN)

    def test_ips_publicado(self):
        """El IPS de ips/ lleva la ROM a la imagen de referencia."""
        juego, ROM = self.juego, self.rom()
        img = ips.aplica((RAIZ / juego.IPS).read_bytes(), ROM.read_bytes())
        self.assertEqual(hashlib.sha256(img).hexdigest(), juego.SHA256_IMAGEN)



class EnsambladoOriginal(Ensamblado, unittest.TestCase):
    juego = juego


class EnsambladoEnhanced(Ensamblado, unittest.TestCase):
    juego = juego_enhanced


class ParcheadorOriginal(Parcheador, unittest.TestCase):
    juego = juego


class ParcheadorEnhanced(Parcheador, unittest.TestCase):
    juego = juego_enhanced


if __name__ == "__main__":
    unittest.main()
