;==============================================================================
; galious_driver.asm — The Maze of Galious: 3 save slots in Yamanooto flash
;------------------------------------------------------------------------------
; Appended to the 128KB game as relative bank 0x10 and called through the bank
; 3 shim (galious_shim.asm) with the driver mapped at 0x8000, under DI. The
; save sector is relative bank 0x18 (mapped at 0xA000 only while the driver
; reads/writes it; bank 3 is put back from the shadow 0xF0F3 before returning,
; because the shim runs from there).
;
; What is saved is the game's own password: the 45 letters (codes 0x01-0x24)
; that hace_la_contrasena (p02:95A0) leaves at 0xEB40. Loading copies them to
; 0xEB00, the buffer the typing screen fills, and raises 0xE02D like RETURN:
; the game then checks them with its own sum (p02:97DD) and restores the game
; (p02:982B), so a bad record just shows the game's "wrong password" text.
;
;   fn 0  save menu  : message area (RAM copy 0xEE26, rows of 32) = the prompt
;                      and the state of the 3 slots; remembers the keyboard.
;   fn 1  save key   : 1/2/3 newly pressed -> write that slot. NZ = saved,
;                      Z = keep waiting (no key, or FLASH ERROR shown).
;   fn 2  load frame : the 3 slots on screen (VRAM rows 8/10/12, column 8,
;                      under "LOAD WHICH SLOT?" / "PRESS 1 2 OR 3" drawn over
;                      the game's own two lines at rows 4 and 6);
;                      1/2/3 newly pressed on a used slot -> letters to 0xEB00
;                      and 0xE02D = 1.
;
; Slot record at sector offset slot*0x40: [0xA5][45 letters]; 0xFF = empty.
; RAM (free in play, measured): engine 0xF100, staging 0xF200, vars 0xF2C0.
;
; Build: pasmo --bin galious_driver.asm galious_driver.bin   (8192 bytes)
;==============================================================================

SCC_REG_6000 equ 0x7000    ; Konami-SCC registers of the 0x6000 and 0xA000 windows
SCC_REG_A000 equ 0xB000
BankIn60    equ 0xF0F1
BankInA0    equ 0xF0F3
SAVE_BANK   equ 0x18
ENGINE      equ 0xF100
STAGE       equ 0xF200
STAGE_LEN   equ 0x00C0
SLOT_STRIDE equ 0x40
MARK        equ 0xA5
NLETTERS    equ 45
VAR_PREV    equ 0xF2C0      ; keyboard row 0 seen last time (active low)
TXTBUF      equ 0xF2C1      ; one slot line, 0-terminated (15 bytes)

LETTERS     equ 0xEB40      ; the password made by hace_la_contrasena
TYPED       equ 0xEB00      ; the buffer the typing screen fills
DONE        equ 0xE02D      ; state 0x12: RETURN pressed
MSG_AREA    equ 0xEE26      ; message area of the special rooms (RAM copy)
VRAM_ROWS   equ 0x3908      ; the three password rows of the typing screen

    org 0x8000

entry:
    ld   a, c
    or   a
    jp   z, save_menu
    dec  a
    jp   z, save_key
    jp   load_frame

;------------------------------------------------------------------------------
; fn 0: the prompt and the 3 slots in the message area
save_menu:
    call clear_msgs
    ld   hl, txt_which
    ld   de, MSG_AREA
    call put_ram
    ld   b, 0
sm_slot:
    push bc
    call slot_text          ; HL = "SLOT n  USED " / "SLOT n  EMPTY"
    ld   a, b               ; DE = 0xEE66 + slot*0x20
    rrca
    rrca
    rrca
    add  a, 0x66
    ld   e, a
    ld   d, 0xEE
    call put_ram
    pop  bc
    inc  b
    ld   a, b
    cp   3
    jr   nz, sm_slot
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
    ld   e, a
    ld   d, STAGE / 256
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
    ld   hl, txt_error
    ld   de, MSG_AREA
    call put_ram
sk_wait:
    xor  a                  ; Z: keep waiting
    ret

;------------------------------------------------------------------------------
; fn 2: one frame of the load menu
load_frame:
    ld   hl, 0x3887         ; over the game's "ENTER THE SECRET" (row 4)...
    call set_vram
    ld   hl, txt_load
    call put_vram
    ld   hl, 0x38C7         ; ...and "RETURN KEY!" (row 6), both languages
    call set_vram
    ld   hl, txt_press
    call put_vram
    ld   b, 0
lf_slot:
    push bc
    ld   a, b               ; VRAM 0x3908 + slot*0x40
    rrca
    rrca
    add  a, VRAM_ROWS - 0x3900
    out  (0x99), a
    ld   a, 0x40 + VRAM_ROWS / 256
    out  (0x99), a
    call slot_text
    call put_vram
    pop  bc
    inc  b
    ld   a, b
    cp   3
    jr   nz, lf_slot
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
; HL = "SLOT n  USED " or "SLOT n  EMPTY" for slot B (built in TXTBUF).
; Keeps B and DE.
slot_text:
    ld   a, b
    call slot_addr
    ld   a, (hl)
    call unmap_save
    ld   hl, txt_used
    cp   MARK
    jr   z, st_used
    ld   hl, txt_empty
st_used:
    push bc
    push de
    push hl
    ld   hl, txt_slot
    ld   de, TXTBUF
    ld   bc, 8
    ldir
    pop  hl
    ld   bc, 6
    ldir
    pop  de
    pop  bc
    ld   a, b
    add  a, '1'
    ld   (TXTBUF+5), a
    ld   hl, TXTBUF
    ret

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

; VRAM write address = HL (DI held by the shim)
set_vram:
    ld   a, l
    out  (0x99), a
    ld   a, h
    or   0x40
    out  (0x99), a
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

; 5 rows of 20 from 0xEE26 to blank
clear_msgs:
    ld   hl, MSG_AREA
    ld   c, 5
cm_row:
    ld   b, 20
cm_col:
    ld   (hl), 0
    inc  hl
    djnz cm_col
    ld   de, 12
    add  hl, de
    dec  c
    jr   nz, cm_row
    ret

; ASCII text at HL (0-terminated) to the game's font: to RAM at DE...
put_ram:
    ld   a, (hl)
    or   a
    ret  z
    call font
    ld   (de), a
    inc  hl
    inc  de
    jr   put_ram
; ...or to the VRAM address already set
put_vram:
    ld   a, (hl)
    or   a
    ret  z
    call font
    out  (0x98), a
    inc  hl
    jr   put_vram

; ' ' 0, '0'-'9' 1-10, 'A'-'Z' 11-36, '?' 0x29 (as typed: p02:9741)
font:
    cp   ' '
    jr   nz, f_q
    xor  a
    ret
f_q:
    cp   '?'
    jr   nz, f_l
    ld   a, 0x29
    ret
f_l:
    cp   'A'
    jr   c, f_d
    sub  0x36
    ret
f_d:
    sub  0x2F
    ret

txt_which:  defb "SAVE IN WHICH SLOT?", 0
txt_load:   defb "LOAD WHICH SLOT?   ", 0
txt_press:  defb "PRESS 1 2 OR 3     ", 0
txt_error:  defb "FLASH ERROR        ", 0
txt_slot:   defb "SLOT 1  "
txt_used:   defb "USED ", 0
txt_empty:  defb "EMPTY", 0

engine_bin:
    incbin "galious_engine.bin"
engine_end:
engine_len  equ engine_end - engine_bin

    ds   0xA000 - $, 0xFF
    end
