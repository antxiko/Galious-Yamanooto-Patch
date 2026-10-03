#!/usr/bin/env python3
"""Patch The Maze of Galious (RC749, 128KB Konami-4) so it saves to and loads
from 3 slots in Yamanooto flash instead of showing/typing the password.

- Password room (special room type 1), after YES: no password on screen;
  "SAVE IN WHICH SLOT?" and the state of the 3 slots; keys 1/2/3 save.
- Title + L (state 0x12): instead of the typing screen, the 3 slots; keys
  1/2/3 load. The game checks the loaded password with its own sum and
  restores the game exactly as if it had been typed.

Three call sites of bank 2 are repointed at stubs written into bank 3's free
0xFF tail (galious_shim.bin at ROM 0x7F93 = CPU 0xBF93), and the 8KB driver
(galious_driver.bin) is appended as game-relative bank 0x10. Pack the result
with `mapper = "galious"`: 256KB footprint, 64KB save sector at relative bank
0x18 (the same layout as "mg1").

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
