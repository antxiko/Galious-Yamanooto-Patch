;==============================================================================
; galious_shim.asm — three stubs + common shim, patched into Galious' bank 3
;------------------------------------------------------------------------------
; galious_to_yamanooto.py writes this blob into the free 0xFF tail of bank 3
; (ROM 0x7F93 = CPU 0xBF93, 93 bytes before the Konami mark at 0xBFF0). Bank 3
; sits at 0xA000 while the password code of bank 2 (0x8000) runs. Three sites
; of bank 2 are repointed at the stubs (5 bytes each, fixed addresses):
;     0xBF93  fn 0  save menu   (password room, after YES: p02:90F8)
;     0xBF98  fn 1  save key    (password room, step 2: p02:910D, Z = wait)
;     0xBF9D  fn 2  load frame  (state 0x12, replaces p02:9716)
; The common shim maps the driver bank (0x10) into the 0x8000 window and calls
; it with C = fn id under DI (the interrupt hook p00:40EF and pide_sonido put
; banks 13/14 in 0x6000/0x8000 and restore them from the shadows), then puts
; bank 2 back from the game's own shadow and returns the driver's A + flags.
;
; Build: pasmo --bin galious_shim.asm galious_shim.bin   (org 0xBF93, max 93 B)
;==============================================================================

K4_REG_8000 equ 0x8000
BankIn80    equ 0xF0F2      ; Galious' shadow of the 0x8000 window (= 2 here)
DRIVER_BANK equ 0x10
DRIVER      equ 0x8000

    org 0xBF93

stub_save_menu:             ; 0xBF93
    push bc
    ld   c, 0
    jr   common
stub_save_key:              ; 0xBF98
    push bc
    ld   c, 1
    jr   common
stub_load:                  ; 0xBF9D
    push bc
    ld   c, 2
    jr   common

common:                     ; 0xBFA2
    push de
    push hl
    di
    ld   a, DRIVER_BANK
    ld   (K4_REG_8000), a   ; map the driver into window 2
    call DRIVER             ; C = fn -> returns A + flags
    push af
    ld   a, (BankIn80)
    ld   (K4_REG_8000), a   ; put Galious' bank back
    pop  af
    pop  hl
    pop  de
    pop  bc
    ei
    ret
shim_end:
    end
