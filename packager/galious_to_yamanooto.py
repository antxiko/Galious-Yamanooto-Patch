#!/usr/bin/env python3
"""Patch The Maze of Galious (RC749, 128KB Konami-4) so it saves to and loads
from 3 slots in Yamanooto flash instead of showing/typing the password.

- Password room (special room type 1), after YES: no password on screen;
  "SAVE IN WHICH SLOT?" and the state of the 3 slots; keys 1/2/3 save.
- Title + L (state 0x12): instead of the typing screen, the 3 slots; keys
  1/2/3 load. The game checks the loaded password with its own sum and
  restores the game exactly as if it had been typed.

Three call sites of bank 2 are repointed at stubs written into bank 3's free
0xFF tail (galious_shim.bin at ROM 0x7F93 = CPU 0xBF93), the game's 32 bank
switches are moved from the Konami-4 registers to the Konami-SCC ones (the
mode a Yamanooto starts in), and the 8KB driver (galious_driver.bin) is
appended as game-relative bank 0x10. The 64KB save sector is relative bank
0x18: flashed at offset 0 with that sector blank (tools/imagen.py), the game
boots and saves on its own.

Addresses come from the annotated disassembly (antxiko/MazeOfGalious-
disassembly). Every patched site is checked against the original bytes and
the script refuses on any mismatch, so it can never corrupt an unknown dump.

Usage:
    python packager/galious_to_yamanooto.py "Maze of Galious.rom" galious_yama.rom
"""
import hashlib
import sys
from pathlib import Path

ROM_SIZE = 0x20000
SHA256 = "420c42c18006eb5d"          # first 16 hex digits of the known dump
SHIM_OFFSET = 0x7F93                 # bank 3 free tail (CPU 0xBF93), 93 bytes
SHIM_MAX = 0x7FF0 - SHIM_OFFSET      # up to the Konami mark at 0xBFF0
STUB_SAVE_MENU, STUB_SAVE_KEY, STUB_LOAD = 0xBF93, 0xBF98, 0xBF9D


def lo_hi(a):
    return [a & 0xFF, a >> 8]


# (what, ROM offset, original bytes, new bytes) — bank 2 runs at 0x8000:
# ROM offset = 0x4000 + (CPU - 0x8000)
SITES = [
    ("p02:90F5 password room, YES: message 15 + password -> password + save menu",
     0x50F5, bytes.fromhex("3E0FCDEF94CDA095"),
     bytes([0xCD, 0xA0, 0x95, 0xCD] + lo_hi(STUB_SAVE_MENU) + [0x00, 0x00])),
    ("p02:910D password room, step 2: button A -> keys 1/2/3 save",
     0x510D, bytes.fromhex("3A08E0E610C8"),
     bytes([0xCD] + lo_hi(STUB_SAVE_KEY) + [0x00, 0x00, 0xC8])),
    ("p02:9716 typing screen (state 0x12) -> load menu",
     0x5716, bytes.fromhex("CD5797CD6F97CD2297C3AF97"),
     bytes([0xC3] + lo_hi(STUB_LOAD)) + bytes.fromhex("CD6F97CD2297C3AF97")),
]


# The game's 32 bank switches, all `ld (6000h/8000h/A000h),a` in bank 0 (the
# Konami-4 registers). Each gets the Konami-SCC register of the same window
# (7000h/9000h/B000h): the high byte of the operand. That is the mode a
# Yamanooto starts in, so the patched game boots straight from flash offset 0,
# with no menu and no boot code. ROM offsets of the `32 nn nn` opcodes:
MAPPER_SITES = [
    0x0103, 0x0107, 0x0115, 0x011B, 0x016F, 0x0176, 0x017D, 0x0188,
    0x018F, 0x0196, 0x01A1, 0x01A8, 0x01AF, 0x01BA, 0x01C1, 0x01C8,
    0x01D3, 0x01DA, 0x01E1, 0x01EC, 0x01F7, 0x0202, 0x020D, 0x0218,
    0x0223, 0x022E, 0x0239, 0x0244, 0x0E47, 0x0E4B, 0x0E59, 0x0E62,
]
K4_TO_SCC = {0x60: 0x70, 0x80: 0x90, 0xA0: 0xB0}


def patch(rom: bytes, shim: bytes, driver: bytes) -> bytes:
    if len(rom) != ROM_SIZE:
        raise SystemExit(f"ROM must be {ROM_SIZE} bytes (128KB), got {len(rom)}")
    if len(shim) > SHIM_MAX:
        raise SystemExit(f"shim too big: {len(shim)} > {SHIM_MAX}")
    if len(driver) != 0x2000:
        raise SystemExit(f"driver must be 8192 bytes, got {len(driver)}")
    if set(rom[SHIM_OFFSET:SHIM_OFFSET + SHIM_MAX]) != {0xFF}:
        raise SystemExit("bank 3 free tail is not 0xFF filler — unknown dump, refusing")

    data = bytearray(rom)
    for what, off, old, new in SITES:
        got = bytes(data[off:off + len(old)])
        if got != old:
            raise SystemExit(f"{what} @0x{off:05X}: expected {old.hex()}, found "
                             f"{got.hex()} — unknown dump, refusing (nothing written)")
        data[off:off + len(new)] = new
    for off in MAPPER_SITES:
        got = bytes(data[off:off + 3])
        if got[0] != 0x32 or got[1] != 0x00 or got[2] not in K4_TO_SCC:
            raise SystemExit(f"bank switch @0x{off:05X}: expected 32 00 60/80/A0, found "
                             f"{got.hex()} — unknown dump, refusing (nothing written)")
        data[off + 2] = K4_TO_SCC[got[2]]
    data[SHIM_OFFSET:SHIM_OFFSET + len(shim)] = shim
    return bytes(data) + driver


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    rom_path, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    here = Path(__file__).resolve().parent.parent / "launcher"
    rom = rom_path.read_bytes()
    shim = (here / "galious_shim.bin").read_bytes()
    driver = (here / "galious_driver.bin").read_bytes()

    sha = hashlib.sha256(rom).hexdigest()
    note = "" if sha.startswith(SHA256) else "  (not the known dump: sites checked one by one)"
    print(f"input : {rom_path.name}  sha256={sha[:16]}...{note}")
    out = patch(rom, shim, driver)
    out_path.write_bytes(out)
    print(f"output: {out_path} ({len(out)} bytes = 128KB game + 8KB driver)")
    print(f"  {len(SITES)} sites -> stubs @0x{STUB_SAVE_MENU:04X}, shim {len(shim)}B "
          f"@ROM 0x{SHIM_OFFSET:05X}, driver = relative bank 0x10")
    print('Pack with mapper = "galious" (256KB footprint, save sector at rel bank 0x18).')


if __name__ == "__main__":
    main()
