# The Maze of Galious — saves on the Yamanooto

*[Español](README.es.md)*

The game keeps your progress in a **45-letter password** that you have to write down. With this patch, in the password room you pick **one of three slots** and the game is saved to the cartridge's flash. On the title screen, L no longer takes you to the typing screen: you get the slot menu. What gets saved is those same 45 letters, and **the game checks them with its own checksum**, as if they had been typed.

**55** bytes changed in **4** stretches · **8 KB** driver · 3 slots in **one 64 KB sector** · no ROM distributed

## How to play

- **Save:** in the password room answer YES. Instead of the password you get *SAVE IN WHICH SLOT?* with the three slots (*USED* or *EMPTY*); press 1, 2 or 3.
- **Load:** on the title screen press L. Instead of the typing screen you get *LOAD WHICH SLOT?*; press the slot number.

A damaged slot breaks nothing: it gives the game's own *THAT IS THE WRONG...*, like a mistyped password.

## What you need

- **The game ROM**, which this repository does not distribute: *The Maze of Galious* (Konami, 1987, RC-749), 131,072 bytes, sha256 `420c42c18006eb5dbb25efa5b83e340d740824c15a714929a945c0db51f97280`.
- **Python 3.**
- **A Yamanooto**, 2 MB or 8 MB.

## Building the image

```
python tools/imagen.py galious.rom
```

You get `galious_yamanooto_2MB.rom`, ready to flash. **Flashing it replaces the menu and games on the cartridge.** In openMSX:

```
openmsx -cart galious_yamanooto_2MB.rom -romtype Yamanooto
```

`make test` runs the 6 tests: the `.bin` files come from their `.asm`, the menu carries nothing of the game, the patcher refuses another ROM and, with the ROM in the root, outside the stretches the patcher declares the game is the original byte for byte and the image is the reference one.

## How it works

- Three places in bank 2 (p02:90F5, p02:910D and p02:9716) call three entry points written into bank 3's filler: 39 bytes at 0xBF93, before the Konami mark.
- Those entry points put the driver ([launcher/galious_driver.asm](launcher/galious_driver.asm), 8 KB appended as bank 0x10) in the 0x8000 window with interrupts off, because the game's interrupt switches banks for the sound.
- Each slot is `[0xA5][45 letters]` in a 64 KB flash sector (relative bank 0x18). To change one, the start of the sector is copied to RAM, the sector is erased, reprogrammed and read back to check it; if it does not match, *FLASH ERROR*.
- The RAM it uses (0xF100-0xF2CF) is measured: in a 35,812-frame game nothing is written between 0xF0F9 and 0xF37F.
- The addresses come from the [annotated disassembly of The Maze of Galious](https://antxiko.github.io/MazeOfGalious-disassembly/). The patcher checks the original bytes of every site and refuses to write if they do not match.

## Where it comes from

It is a piece of [nPackR](https://github.com/antxiko/msx-yamanooto-npackr), which uses it to put the game in a collection. Here it comes on its own, with nPackR's menu already set up for this game. GPL v3 licence ([LICENSE](LICENSE)) and a non-commercial note ([NOTICE.md](NOTICE.md)).

## Tested

In openMSX; not yet on a real cartridge.
