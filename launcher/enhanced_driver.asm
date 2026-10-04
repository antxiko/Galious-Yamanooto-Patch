;==============================================================================
; enhanced_driver.asm — The Maze of Galious Enhanced: 3 save slots in
; Yamanooto flash
;------------------------------------------------------------------------------
; Written over bank 0x0C of the Enhanced (8KB of 0xFF that nothing maps) and
; called through the bank 3 shim (enhanced_shim.asm) with the driver mapped at
; 0x8000, under DI. The save sector is relative bank 0x40, right after the
; 512KB game (mapped at 0xA000 only while the driver reads/writes it; bank 3
; is put back from the shadow 0xF0F3 before returning: the shim runs there).
;
; What is saved is the game's own password: the 45 letters (codes 0x01-0x24)
; that hace_la_contrasena (p02:9392) leaves at 0xEB40, the same as in the
; original. Loading copies them to 0xEB00, the buffer the typing screen
; fills, and raises 0xE02D like RETURN: the game checks them with its own sum
; and restores the game, so a bad record just shows its "wrong password".
;
; The driver cannot draw (see the shim): it writes ASCII text to TXT (0xFE =
; next row, 0xFF = end) and the position to DRAW_POS, and the shim draws it
; with the game's own routine and font.
;
;   fn 0  save menu  : clear the message box, then the prompt and the state
;                      of the 3 slots there; blanks the YES/NO hand, drawn in
;                      the bitmap at rows 17-18, column 9 (the slot is chosen
;                      with the number keys); remembers the keyboard.
;   fn 1  save key   : 1/2/3 newly pressed -> write that slot. NZ = saved,
;                      Z = keep waiting (no key, or FLASH ERROR shown).
;   fn 2  load frame : the first frame of the typing screen (LOAD_FLAG, in
;                      the buffer the game zeroes on entry) draws the prompt
;                      over the game's three lines and the 3 slots under it;
;                      1/2/3 newly pressed on a used slot -> letters to 0xEB00
;                      and 0xE02D = 1.
;
; Slot record at sector offset slot*0x40: [0xA5][45 letters]; 0xFF = empty.
; RAM (free in play, measured): engine 0xF110, staging and text 0xF1A0,
; vars 0xF260.
;
; Build: pasmo --bin enhanced_driver.asm enhanced_driver.bin   (8192 bytes)
;==============================================================================

SCC_REG_6000 equ 0x7000    ; Konami-SCC registers of the 0x6000 and 0xA000 windows
SCC_REG_A000 equ 0xB000
BankIn60    equ 0xF0F1
BankInA0    equ 0xF0F3
SAVE_BANK   equ 0x40
ENGINE      equ 0xF110
STAGE       equ 0xF1A0
STAGE_LEN   equ 0x00C0
SLOT_STRIDE equ 0x40
MARK        equ 0xA5
NLETTERS    equ 45

TXT         equ 0xF1A0      ; text for the shim (shares STAGE: never both)
VAR_PREV    equ 0xF260      ; keyboard row 0 seen last time (active low)
DRAW_POS    equ 0xF262      ; word, read by the shim
DRAW_CLR    equ 0xF264
DRAW_MODE   equ 0xF265

LETTERS     equ 0xEB40      ; the password made by hace_la_contrasena
TYPED       equ 0xEB00      ; the buffer the typing screen fills
LOAD_FLAG   equ 0xEBF0      ; zeroed with 0xEB00-0xEBFF on entry (p02:94FE)
DONE        equ 0xE02D      ; state 0x12: RETURN pressed

; Positions for the game's text routine: H >= 0xE0 means name-table address
; + 0xB500, and then each 0xFE goes to the next row.
POS_SAVE    equ 0xEE26      ; row 9, column 6: where the password goes
POS_ERROR   equ 0xEEC6      ; row 14, column 6: where "Did you memorize it?" goes
POS_LOAD    equ 0xED87      ; row 4, column 7: "Enter the secret password..."

    org 0x8000

entry:
    ld   a, c
    or   a
    jp   z, save_menu
    dec  a
    jp   z, save_key
    jp   load_frame

;------------------------------------------------------------------------------
; fn 0: clear the box, then the prompt and the 3 slots in it
save_menu:
    ld   de, TXT
    ld   hl, txt_which
    call copy
    ld   a, 0xFE            ; a blank row
    ld   (de), a
    inc  de
    call slot_lines
    ld   hl, txt_hand
    call copy
    ld   a, 0xFF
    ld   (de), a
    ld   hl, POS_SAVE
    ld   a, 3
    ld   c, 1
    call draw
    call read_row0
    ld   (VAR_PREV), a
    ret

;------------------------------------------------------------------------------
; fn 1: wait for 1/2/3, then write the slot. NZ = saved.
save_key:
    call key_slot
    cp   0xFF
    jr   z, sk_wait
    ld   b, a
    push bc
    call map_save           ; staging = the sector's first 0xC0 bytes
    ld   hl, 0xA000
    ld   de, STAGE
    ld   bc, STAGE_LEN
    ldir
    call unmap_save
    pop  bc
    ld   a, b               ; DE = STAGE + slot*0x40
    rrca
    rrca
    ld   l, a
    ld   h, 0
    ld   de, STAGE
    add  hl, de
    ex   de, hl
    ld   a, MARK
    ld   (de), a
    inc  de
    ld   hl, LETTERS
    ld   bc, NLETTERS
    ldir
    ld   hl, engine_bin     ; the engine must run from RAM
    ld   de, ENGINE
    ld   bc, engine_len
    ldir
    call ENGINE
    ld   a, (BankIn60)      ; in case the Yamanooto register writes moved it
    ld   (SCC_REG_6000), a
    call map_save           ; verify: the sector must read back as staged
    ld   hl, 0xA000
    ld   de, STAGE
    ld   b, STAGE_LEN
sk_cmp:
    ld   a, (de)
    cp   (hl)
    jr   nz, sk_bad
    inc  hl
    inc  de
    djnz sk_cmp
    call unmap_save
    ld   a, 1
    or   a                  ; NZ: saved
    ret
sk_bad:
    call unmap_save
    ld   de, TXT
    ld   hl, txt_error
    call copy
    ld   a, 0xFF
    ld   (de), a
    ld   hl, POS_ERROR
    ld   a, 3
    ld   c, 0
    call draw
sk_wait:
    xor  a                  ; Z: keep waiting
    ret

;------------------------------------------------------------------------------
; fn 2: one frame of the load menu
load_frame:
    ld   a, (LOAD_FLAG)
    cp   MARK
    jr   z, lf_keys
    ld   a, MARK
    ld   (LOAD_FLAG), a
    ld   de, TXT
    ld   hl, txt_load
    call copy
    call slot_lines
    ld   a, 0xFF
    ld   (de), a
    ld   hl, POS_LOAD
    xor  a
    ld   c, 0
    call draw
    call read_row0
    ld   (VAR_PREV), a
    ret
lf_keys:
    call key_slot
    cp   0xFF
    ret  z
    call slot_addr          ; HL = record in the sector (mapped)
    ld   a, (hl)
    cp   MARK
    jr   nz, lf_none
    inc  hl
    ld   de, TYPED
    ld   bc, NLETTERS
    ldir
    call unmap_save
    ld   a, 1
    ld   (DONE), a
    ret
lf_none:
    jp   unmap_save

;------------------------------------------------------------------------------
; tell the shim: draw TXT at HL with style A; C = 1: clear the box first
draw:
    ld   (DRAW_POS), hl
    ld   (DRAW_MODE), a
    ld   a, c
    ld   (DRAW_CLR), a
    ret

; at DE: for each slot, 0xFE + "Slot n  used " / "Slot n  empty" (no end)
slot_lines:
    ld   b, 0
sl_slot:
    ld   a, 0xFE
    ld   (de), a
    inc  de
    ld   hl, txt_slot
    call copy
    dec  de                 ; the slot number goes over the '1'
    dec  de
    dec  de
    ld   a, b
    add  a, '1'
    ld   (de), a
    inc  de
    inc  de
    inc  de
    ld   a, b
    call slot_addr
    ld   a, (hl)
    call unmap_save
    ld   hl, txt_used
    cp   MARK
    jr   z, sl_used
    ld   hl, txt_empty
sl_used:
    call copy
    inc  b
    ld   a, b
    cp   3
    jr   nz, sl_slot
    ret

; copy the 0-terminated text at HL to DE (DE ends after it). Keeps B.
copy:
    ld   a, (hl)
    or   a
    ret  z
    ld   (de), a
    inc  hl
    inc  de
    jr   copy

; HL = 0xA000 + A*0x40 with the save sector mapped at 0xA000
slot_addr:
    rrca
    rrca
    ld   l, a
    ld   h, 0xA0
map_save:
    ld   a, SAVE_BANK
    ld   (SCC_REG_A000), a
    ret
unmap_save:
    push af
    ld   a, (BankInA0)
    ld   (SCC_REG_A000), a
    pop  af
    ret

; A = keyboard row 0 (active low); bits 1/2/3 = keys 1/2/3
read_row0:
    in   a, (0xAA)
    and  0xF0
    out  (0xAA), a
    in   a, (0xA9)
    ret

; A = slot 0-2 whose key was just pressed, or 0xFF
key_slot:
    call read_row0
    ld   b, a
    ld   a, (VAR_PREV)
    ld   c, a
    ld   a, b
    ld   (VAR_PREV), a
    cpl                     ; pressed now...
    and  c                  ; ...and released last time
    ld   b, a
    xor  a
    bit  1, b
    ret  nz
    inc  a
    bit  2, b
    ret  nz
    inc  a
    bit  3, b
    ret  nz
    ld   a, 0xFF
    ret

; the game's own font, in its own mixed case
txt_which:  defb "Save in which slot?", 0
txt_load:   defb "Load which slot?    ", 0xFE
            defb "Press 1, 2 or 3     ", 0xFE
            defb "                    ", 0xFE, 0
txt_hand:   defb 0xFE, 0xFE, 0xFE, 0xFE, "    "  ; rows 14-17: the hand's top...
            defb 0xFE, "    ", 0                 ; ...and row 18 (columns 6-9)
txt_error:  defb "Flash error         ", 0
txt_slot:   defb "Slot 1  ", 0
txt_used:   defb "used ", 0
txt_empty:  defb "empty", 0

engine_bin:
    incbin "enhanced_engine.bin"
engine_end:
engine_len  equ engine_end - engine_bin

    ds   0xA000 - $, 0xFF
    end
