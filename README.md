# The Maze of Galious — saves on the Yamanooto

*[Español](README.es.md)*

The game keeps your progress in a **45-letter password** that you have to write down. With this patch, in the password room you pick **one of three slots** and the game is saved to the cartridge's flash. On the title screen, L no longer takes you to the typing screen: you get the slot menu. What gets saved is those same 45 letters, and **the game checks them with its own checksum**, as if they had been typed.

**87** bytes changed in **36** stretches · **8 KB** driver · 3 slots in **one 64 KB sector** · no ROM distributed

## How to play

- **Save:** in the password room answer YES. Instead of the password you get *SAVE IN WHICH SLOT?* with the three slots (*USED* or *EMPTY*); press 1, 2 or 3.
- **Load:** on the title screen press L. Instead of the typing screen you get *LOAD WHICH SLOT?*; press the slot number, or **ESC** to go back to the title.

A damaged slot breaks nothing: it gives the game's own *THAT IS THE WRONG...*, like a mistyped password.

## What you need

- **The game ROM**, which this repository does not distribute: *The Maze of Galious* (Konami, 1987, RC-749), 131,072 bytes, sha256 `420c42c18006eb5dbb25efa5b83e340d740824c15a714929a945c0db51f97280`.
- **Python 3.**
- **A Yamanooto**, 2 MB or 8 MB.

For the second edition, *The Maze of Galious Enhanced*, see below.

## Building the image

```
python tools/imagen.py galious.rom
```

You get `galious_yamanooto.rom` (256 KB), ready to flash from the start of the flash: it boots the game on its own, with no menu. **Flashing it replaces the menu and games on the cartridge.** In openMSX:

```
openmsx -cart galious_yamanooto.rom -romtype Yamanooto
```

**Without Python:** apply [ips/galious_yamanooto.ips](ips/galious_yamanooto.ips) (1028 bytes) to the ROM with any IPS tool (Lunar IPS, Floating IPS, RomPatcher.js) and you get the same image. It only carries what the patch changes, nothing of the game.

`make test` runs the 10 tests, 5 per edition: the `.bin` files come from their `.asm`, the patcher refuses another ROM and, with the ROM in the root, outside the stretches the patcher declares the game is the original byte for byte, the image is the reference one and the IPS gives that same image.

## The Maze of Galious Enhanced

bladeba's [Enhanced](https://github.com/bladeba/MSX/tree/master/Enhanced%20Games/Galious%20-%20enhanced) (v1.04, for MSX2: new SCREEN 5 graphics, SCC music, 512 KB Konami SCC) saves the same way: the same three slots, keys 1, 2 and 3, and the menus come out in the game's own font. The YES/NO hand does not show in the save menu, because you choose with the numbers.

**94** bytes changed in **10** stretches · **8 KB** driver inside the game · 3 slots in **one 64 KB sector** · **576 KB** image

- **The ROM:** the one above with bladeba's *Galious Enhanced V1.04* IPS applied: 524,288 bytes, sha256 `cdeaa916d198a3ca9891076eb79e05709876fa7ce18dcd929e76f1cf25403f53`. bladeba's IPS is not distributed here either.
- **The image:** `python tools/imagen.py galious_enhanced.rom` gives `galious_enhanced_yamanooto.rom`; the script tells the edition by the ROM's size. Without Python, [ips/galious_enhanced_yamanooto.ips](ips/galious_enhanced_yamanooto.ips) (911 bytes) applied to the Enhanced ROM.
- **Inside:** the Enhanced keeps the original's password, moved inside its bank 2 and with the same RAM. The three sites are p02:8EB9, p02:8ED1 and p02:9510. The shim (85 bytes) goes at the end of bank 3, which the Enhanced leaves zeroed and nothing points to. The driver goes in bank 0x0C, 8 KB left empty: the game maps it at the 0xA000 window but never reads it (measured in openMSX over 5 minutes of demo and play). There are no free 64 KB inside the 512 KB, so the sector goes after it, at relative bank 0x40.
- **The text:** the driver cannot draw, because the game's text routine switches the banks above it. It leaves the text in RAM and the shim draws it with that routine in ASCII mode, as the game does with its English messages.
- **Tested** in openMSX as a Yamanooto and inside an [nPackR](https://github.com/antxiko/msx-yamanooto-npackr) pack (v1.7.4, mapper `galious_enhanced`): save with items in one slot without touching the others, close, reopen and load, and the items come back. Not tested on a real MSX yet.

## How it works

- The game's 32 bank switches (`ld (6000h/8000h/A000h),a`, all in bank 0) move to the Konami SCC registers of the same window (7000h/9000h/B000h): that is the mode a Yamanooto starts in, so the game boots on its own from the start of the flash.
- Three places in bank 2 (p02:90F5, p02:910D and p02:9716) call three entry points written into bank 3's filler: 39 bytes at 0xBF93, before the Konami mark.
- Those entry points put the driver ([launcher/galious_driver.asm](launcher/galious_driver.asm), 8 KB appended as bank 0x10) in the 0x8000 window with interrupts off, because the game's interrupt switches banks for the sound.
- Each slot is `[0xA5][45 letters]` in a 64 KB flash sector (relative bank 0x18). To change one, the start of the sector is copied to RAM, the sector is erased, reprogrammed and read back to check it; if it does not match, *FLASH ERROR*.
- The RAM it uses (0xF100-0xF2CF) is measured: in a 35,812-frame game nothing is written between 0xF0F9 and 0xF37F.
- The addresses come from the [annotated disassembly of The Maze of Galious](https://antxiko.github.io/MazeOfGalious-disassembly/). The patcher checks the original bytes of every site and refuses to write if they do not match.

## Where it comes from

It comes from [nPackR](https://github.com/antxiko/msx-yamanooto-npackr), which uses it to put the game in a collection. Here it comes on its own: the image boots the game directly, with no menu. GPL v3 licence ([LICENSE](LICENSE)) and a non-commercial note ([NOTICE.md](NOTICE.md)).

## Tested

In openMSX and on a real MSX with a real Yamanooto: pabibiris tested it and approves it.
