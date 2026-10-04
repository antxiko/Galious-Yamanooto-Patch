;==============================================================================
; enhanced_engine.asm — the same engine for The Maze of Galious Enhanced
; (bladeba v1.04, 512KB Konami-SCC, MSX2). Only the addresses change: the
; save sector is relative bank 0x40 (right after the 512KB game) and the
; engine/staging sit in RAM the Enhanced leaves alone in play (0xF10A-0xF29B,
; measured with an openMSX write watchpoint, 2026-10-04).
; Build: pasmo --bin enhanced_engine.asm enhanced_engine.bin   (org 0xF110)
;==============================================================================

YAMA_ENAR    equ 0x7FFF
ENAR_WREN    equ 0x10
SCC_REG_A000 equ 0xB000     ; Konami-SCC bank register for the 0xA000-0xBFFF window
SAVE_BANK    equ 0x40       ; the game's 64KB save sector (first bank)
STAGE        equ 0xF1A0     ; raw staged copy of the sector's first 0xC0 bytes
STAGE_LEN    equ 0x00C0     ; 3 slots x 0x40

    org 0xF110

engine:
    ld   a, SAVE_BANK
    ld   (SCC_REG_A000), a   ; map the sector (BEFORE WREN: banking freezes)
    ld   a, ENAR_WREN
    ld   (YAMA_ENAR), a
    call erase_sector
    jr   c, e_fail
    ld   hl, STAGE
    ld   de, 0xA000
    ld   bc, STAGE_LEN
e_loop:
    ld   a, b
    or   c
    jr   z, e_ok
    ld   a, (hl)
    cp   0xFF
    jr   z, e_skip
    push bc
    ld   c, a
    call pgm
    pop  bc
    jr   c, e_fail
e_skip:
    inc  hl
    inc  de
    dec  bc
    jr   e_loop
e_ok:
    xor  a
    ld   (YAMA_ENAR), a
    ret
e_fail:
    xor  a
    ld   (YAMA_ENAR), a
    ld   a, 0xFF
    ret

; --- erase the 64KB sector (bank mapped, WREN on). Carry set on timeout. ------
erase_sector:
    ld   a, 0xAA
    ld   (0xAAAA), a
    ld   a, 0x55
    ld   (0xA555), a
    ld   a, 0x80
    ld   (0xAAAA), a
    ld   a, 0xAA
    ld   (0xAAAA), a
    ld   a, 0x55
    ld   (0xA555), a
    ld   a, 0x30
    ld   (0xA000), a        ; sector erase (any address inside the sector)
    ld   bc, 0
er_poll:
    ld   a, (0xA000)
    cp   0xFF
    jr   z, er_done
    ld   d, 8
er_dly:
    dec  d
    jr   nz, er_dly
    dec  bc
    ld   a, b
    or   c
    jr   nz, er_poll
    scf                     ; timeout
    ret
er_done:
    or   a                  ; clear carry
    ret

; --- program one byte: (DE) = C. WREN on. Carry set on failure. ---------------
pgm:
    ld   a, 0xAA
    ld   (0xAAAA), a
    ld   a, 0x55
    ld   (0xA555), a
    ld   a, 0xA0
    ld   (0xAAAA), a
    ld   a, c
    ld   (de), a
    push bc
    ld   b, 0
pg_poll:
    ld   a, (de)
    cp   c
    jr   z, pg_ok
    djnz pg_poll
    pop  bc
    scf
    ret
pg_ok:
    pop  bc
    or   a
    ret
engine_end:
    end
