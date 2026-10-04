#!/usr/bin/env python3
"""Patch The Maze of Galious Enhanced (bladeba v1.04: 512KB Konami-SCC, MSX2)
so it saves to and loads from 3 slots in Yamanooto flash instead of showing/
typing the password. Same behaviour as galious_to_yamanooto.py:

- Password room, after YES: no password on screen; "Save in which slot?" and
  the state of the 3 slots; keys 1/2/3 save.
- Title + L (state 0x12): instead of the typing screen, the 3 slots; keys
  1/2/3 load. The game checks the loaded password with its own sum and
  restores the game exactly as if it had been typed.

The Enhanced keeps the original's password code and RAM, moved inside bank 2,
but draws in SCREEN 5 with its own text routine, so the driver leaves its text
in RAM and the shim draws it with that routine (see launcher/enhanced_*.asm).
Nothing grows: the shim goes in the tail of bank 3 the Enhanced blanks (ROM
0x7E65-0x7FFF, nothing points there) and the driver in bank 0x0C, 8KB of 0xFF
that nothing maps. The game is already Konami-SCC, the mode a Yamanooto
starts in: no bank switch to move. The 64KB save sector is relative bank 0x40,
right after the game (tools/imagen.py): no 64KB block inside the 512KB is free.

Input: the Enhanced ROM, i.e. bladeba's "Galious Enhanced V1.04.ips" applied
to the original RC-749 dump (SHA-1 4d51d3c5...). Every patched site is checked
against the expected bytes and the script refuses on any mismatch.

Usage:
    python packager/enhanced_to_yamanooto.py "Galious Enhanced.rom" out.rom
"""
import hashlib
import sys
from pathlib import Path

ROM_SIZE = 0x80000
SHA1 = "daa6a451561616891bc077a14fa974aee68ca78f"   # v1.04 applied to RC-749
SHIM_OFFSET = 0x7E80                 # bank 3 blanked tail (CPU 0xBE80)
FREE_TAIL = (0x7E65, 0x8000)         # what the Enhanced fills with 0x00
SHIM_MAX = FREE_TAIL[1] - SHIM_OFFSET
DRIVER_OFFSET = 0x0C * 0x2000        # bank 0x0C, all 0xFF in the Enhanced
STUB_SAVE_MENU, STUB_SAVE_KEY, STUB_LOAD = 0xBE80, 0xBE85, 0xBE8A


def lo_hi(a):
    return [a & 0xFF, a >> 8]


# (what, ROM offset, original bytes, new bytes) — bank 2 runs at 0x8000:
# ROM offset = 0x4000 + (CPU - 0x8000)
SITES = [
    ("p02:8EB9 password room, YES: message 15 + password -> password + save menu",
     0x4EB9, bytes.fromhex("3E0FCDD192CD9293"),
     bytes([0xCD, 0x92, 0x93, 0xCD] + lo_hi(STUB_SAVE_MENU) + [0x00, 0x00])),
    ("p02:8ED1 password room, step 2: button A -> keys 1/2/3 save",
     0x4ED1, bytes.fromhex("3A08E0E610C8"),
     bytes([0xCD] + lo_hi(STUB_SAVE_KEY) + [0x00, 0x00, 0xC8])),
    ("p02:9510 typing screen (state 0x12) -> load menu",
     0x5510, bytes.fromhex("CD5995CD7195CD1A95C9"),
     bytes([0xC3] + lo_hi(STUB_LOAD)) + bytes.fromhex("CD7195CD1A95C9")),
]


def patch(rom: bytes, shim: bytes, driver: bytes) -> bytes:
    if len(rom) != ROM_SIZE:
        raise SystemExit(f"ROM must be {ROM_SIZE} bytes (512KB), got {len(rom)}")
    if len(shim) > SHIM_MAX:
        raise SystemExit(f"shim too big: {len(shim)} > {SHIM_MAX}")
    if len(driver) != 0x2000:
        raise SystemExit(f"driver must be 8192 bytes, got {len(driver)}")
    if set(rom[FREE_TAIL[0]:FREE_TAIL[1]]) != {0x00}:
        raise SystemExit("bank 3 tail is not the Enhanced's 0x00 blank — unknown dump, refusing")
    if set(rom[DRIVER_OFFSET:DRIVER_OFFSET + 0x2000]) != {0xFF}:
        raise SystemExit("bank 0x0C is not blank (0xFF) — unknown dump, refusing")

    data = bytearray(rom)
    for what, off, old, new in SITES:
        got = bytes(data[off:off + len(old)])
        if got != old:
            raise SystemExit(f"{what} @0x{off:05X}: expected {old.hex()}, found "
                             f"{got.hex()} — unknown dump, refusing (nothing written)")
        data[off:off + len(new)] = new
    data[SHIM_OFFSET:SHIM_OFFSET + len(shim)] = shim
    data[DRIVER_OFFSET:DRIVER_OFFSET + 0x2000] = driver
    return bytes(data)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    rom_path, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    here = Path(__file__).resolve().parent.parent / "launcher"
    rom = rom_path.read_bytes()
    shim = (here / "enhanced_shim.bin").read_bytes()
    driver = (here / "enhanced_driver.bin").read_bytes()

    sha = hashlib.sha1(rom).hexdigest()
    note = "" if sha == SHA1 else "  (not the known v1.04: sites checked one by one)"
    print(f"input : {rom_path.name}  sha1={sha[:16]}...{note}")
    out = patch(rom, shim, driver)
    out_path.write_bytes(out)
    print(f"output: {out_path} ({len(out)} bytes = the 512KB game, driver in bank 0x0C)")
    print(f"  {len(SITES)} sites -> stubs @0x{STUB_SAVE_MENU:04X}, shim {len(shim)}B "
          f"@ROM 0x{SHIM_OFFSET:05X}")
    print('Pack with mapper = "galious_enhanced" (576KB footprint, save sector at rel bank 0x40).')


if __name__ == "__main__":
    main()
