# The Maze of Galious — partidas en el Yamanooto

El juego guarda la partida en una **contraseña de 45 letras** que hay que apuntar a mano. Con este parche, en la sala de la contraseña se elige **un slot de los tres** y la partida se graba en la flash del cartucho. En el título, la L ya no lleva a teclear: sale el menú de slots. Lo que se graba son esas mismas 45 letras y **el juego las comprueba con su propia suma**, como si se tecleasen.

**87** bytes cambiados en **36** tramos · driver de **8 KB** · 3 slots en **un sector de 64 KB** · no se distribuye ninguna ROM

## Cómo se juega

- **Grabar:** en la sala de la contraseña se responde SÍ. En vez de la contraseña sale *SAVE IN WHICH SLOT?* con los tres slots (*USED* o *EMPTY*), y se pulsa 1, 2 o 3.
- **Cargar:** en el título se pulsa L. En vez de la pantalla de teclear sale *LOAD WHICH SLOT?* y se pulsa el número del slot.

Un slot dañado no rompe nada: da el *THAT IS THE WRONG...* del propio juego, igual que una contraseña mal tecleada.

## Lo que hace falta

- **La ROM del juego**, que este repositorio no distribuye: *The Maze of Galious* (Konami, 1987, RC-749), 131.072 bytes, sha256 `420c42c18006eb5dbb25efa5b83e340d740824c15a714929a945c0db51f97280`.
- **Python 3.**
- **Un Yamanooto** de 2 MB o de 8 MB.

## Montar la imagen

```
python tools/imagen.py galious.rom
```

Sale `galious_yamanooto.rom` (256 KB), lista para grabar en el cartucho desde el principio de la flash: arranca el juego solo, sin menú. **Grabarla sustituye el menú y los juegos que tenga el cartucho.** En openMSX:

```
openmsx -cart galious_yamanooto.rom -romtype Yamanooto
```

`make test` pasa los 4 tests: los `.bin` salen de sus `.asm`, el parcheador rechaza otra ROM y, con la ROM en la raíz, fuera de los tramos que declara el parcheador el juego es el original byte a byte y la imagen es la de referencia.

## Cómo funciona por dentro

- Los 32 cambios de banco del juego (`ld (6000h/8000h/A000h),a`, todos en el banco 0) pasan a los registros Konami SCC de la misma ventana (7000h/9000h/B000h): es el modo con el que arranca el Yamanooto, así que el juego arranca solo desde el principio de la flash.
- Tres sitios del banco 2 (p02:90F5, p02:910D y p02:9716) llaman a tres entradas escritas en el relleno del banco 3: 39 bytes en 0xBF93, antes de la marca de Konami.
- Esas entradas ponen el driver ([launcher/galious_driver.asm](launcher/galious_driver.asm), 8 KB añadidos como banco 0x10) en la ventana 0x8000 con las interrupciones cortadas, porque la interrupción del juego cambia de banco para el sonido.
- Cada slot es `[0xA5][45 letras]` en un sector de 64 KB de la flash (banco relativo 0x18). Para cambiar uno se copia el principio del sector a la RAM, se borra el sector, se vuelve a programar y se relee para comprobarlo; si no cuadra, *FLASH ERROR*.
- La RAM que usa (0xF100-0xF2CF) está medida: en una partida de 35.812 cuadros el juego no escribe nada entre 0xF0F9 y 0xF37F.
- Las direcciones salen del [desensamblado comentado de The Maze of Galious](https://antxiko.github.io/MazeOfGalious-disassembly/). El parcheador comprueba los bytes originales de cada sitio y se niega a escribir si no cuadran.

## De dónde sale

Sale de [nPackR](https://github.com/antxiko/msx-yamanooto-npackr), que lo usa para meter el juego en una colección. Aquí va suelto: la imagen arranca el juego directamente, sin menú. Licencia GPL v3 ([LICENSE](LICENSE)) y una nota de uso no comercial ([NOTICE.md](NOTICE.md)).

## Probado

En openMSX y en un MSX real con un Yamanooto real: lo probó pabibiris y lo da por bueno.
