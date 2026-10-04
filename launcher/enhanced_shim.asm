;==============================================================================
; enhanced_shim.asm — three stubs + common shim for The Maze of Galious
; Enhanced (bladeba v1.04), patched into the free tail of its bank 3
;------------------------------------------------------------------------------
; The Enhanced patch blanks ROM 0x7E65-0x7FFF (bank 3, CPU 0xBE65-0xBFFF) and
; nothing points there; enhanced_to_yamanooto.py writes this blob at CPU
; 0xBE80. Bank 3 sits at 0xA000 while the password code of bank 2 (0x8000)
; runs. Three sites of bank 2 are repointed at the stubs (fixed addresses):
;     0xBE80  fn 0  save menu   (password room, after YES: p02:8EB9)
;     0xBE85  fn 1  save key    (password room, step 2: p02:8ED1, Z = wait)
;     0xBE8A  fn 2  load frame  (state 0x12, replaces p02:9510)
; The common shim maps the driver bank (0x0C, blank in the Enhanced) into the
; 0x8000 window and calls it with C = fn id under DI (the interrupt code puts
; banks back from the shadows), then puts bank 2 back from the game's own
; shadow. The driver cannot draw: the game's text routine (0x5CB0) maps banks
; 0x19-0x1B over 0x6000-0xBFFF. So it leaves the text in RAM and the shim
; draws it here, after bank 2 is back: first, if asked, the game's own clear
; of the room's message box (p02:9154), then 0x5CB0 with the driver's
; position and style (0x3A20), in ASCII mode (0x272A = 1, as p00:2734). Returns the driver's A + flags.
;
; Build: pasmo --bin enhanced_shim.asm enhanced_shim.bin   (org 0xBE80)
;==============================================================================

SCC_REG_8000 equ 0x9000    ; Konami-SCC register of the 0x8000 window
BankIn80    equ 0xF0F2      ; the game's shadow of the 0x8000 window (= 2 here)
DRIVER_BANK equ 0x0C
DRIVER      equ 0x8000
CLEAR_BOX   equ 0x9154      ; p02: the room's message box to blank (C = 7)
TEXT        equ 0x5CB0      ; p00: HL = position, DE = text, C = 0xFF: draw
TEXT_STYLE  equ 0x3A20      ; 3 in the rooms (set by the game's own messages)
TEXT_ASCII  equ 0x272A      ; 1: ASCII through the game's table (p00:2734)

TXT         equ 0xF1A0      ; the driver's text (FE = next row, FF = end)
DRAW_POS    equ 0xF262      ; word: where to draw it, 0 = nothing to draw
DRAW_CLR    equ 0xF264      ; 1 = blank the message box first
DRAW_MODE   equ 0xF265      ; value for TEXT_STYLE

    org 0xBE80

stub_save_menu:             ; 0xBE80
    push bc
    ld   c, 0
    jr   common
stub_save_key:              ; 0xBE85
    push bc
    ld   c, 1
    jr   common
stub_load:                  ; 0xBE8A
    push bc
    ld   c, 2
    jr   common

common:
    push de
    push hl
    di
    ld   a, DRIVER_BANK
    ld   (SCC_REG_8000), a   ; map the driver into window 2
    call DRIVER             ; C = fn -> returns A + flags
    push af
    ld   a, (BankIn80)
    ld   (SCC_REG_8000), a   ; put the game's bank back
    ei
    ld   a, (DRAW_CLR)
    or   a
    jr   z, no_clear
    xor  a
    ld   (DRAW_CLR), a
    call CLEAR_BOX
no_clear:
    ld   hl, (DRAW_POS)
    ld   a, h
    or   l
    jr   z, no_draw
    ld   de, 0
    ld   (DRAW_POS), de
    ld   a, (DRAW_MODE)
    ld   (TEXT_STYLE), a
    ld   a, 1               ; ASCII, as the English messages (the routine
    ld   (TEXT_ASCII), a    ; puts it back to 0 when done)
    ld   de, TXT
    ld   c, 0xFF
    call TEXT
no_draw:
    pop  af
    pop  hl
    pop  de
    pop  bc
    ret
shim_end:
    end
