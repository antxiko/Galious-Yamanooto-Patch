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

Para la segunda edición, *The Maze of Galious Enhanced*, mira más abajo.

## Montar la imagen

```
python tools/imagen.py galious.rom
```

Sale `galious_yamanooto.rom` (256 KB), lista para grabar en el cartucho desde el principio de la flash: arranca el juego solo, sin menú. **Grabarla sustituye el menú y los juegos que tenga el cartucho.** En openMSX:

```
openmsx -cart galious_yamanooto.rom -romtype Yamanooto
```

**Sin Python:** [ips/galious_yamanooto.ips](ips/galious_yamanooto.ips) (970 bytes) se aplica a la ROM con cualquier herramienta de IPS (Lunar IPS, Floating IPS, RomPatcher.js) y sale la misma imagen. Solo lleva lo que cambia el parche, nada del juego.

`make test` pasa los 10 tests, 5 por edición: los `.bin` salen de sus `.asm`, el parcheador rechaza otra ROM y, con la ROM en la raíz, fuera de los tramos que declara el parcheador el juego es el original byte a byte, la imagen es la de referencia y el IPS da esa misma imagen.

## The Maze of Galious Enhanced

El [Enhanced de bladeba](https://github.com/bladeba/MSX/tree/master/Enhanced%20Games/Galious%20-%20enhanced) (v1.04, para MSX2: gráficos nuevos en SCREEN 5, música SCC, 512 KB Konami SCC) graba igual: los mismos tres huecos, con las teclas 1, 2 y 3, y los menús salen con la letra del propio juego. En el menú de grabar no sale la mano del SÍ/NO, porque se elige con los números.

**94** bytes cambiados en **10** tramos · driver de **8 KB** dentro del juego · 3 huecos en **un sector de 64 KB** · imagen de **576 KB**

- **La ROM:** la de arriba con el IPS *Galious Enhanced V1.04* de bladeba aplicado: 524.288 bytes, sha256 `cdeaa916d198a3ca9891076eb79e05709876fa7ce18dcd929e76f1cf25403f53`. El IPS de bladeba tampoco se distribuye aquí.
- **La imagen:** `python tools/imagen.py galious_enhanced.rom` saca `galious_enhanced_yamanooto.rom`; el script reconoce la edición por el tamaño de la ROM. Sin Python, [ips/galious_enhanced_yamanooto.ips](ips/galious_enhanced_yamanooto.ips) (895 bytes) aplicado a la ROM Enhanced.
- **Por dentro:** el Enhanced conserva la contraseña del original, movida dentro de su banco 2 y con la misma RAM. Los tres sitios son p02:8EB9, p02:8ED1 y p02:9510. El shim (85 bytes) va en el final del banco 3, que el Enhanced deja a ceros y al que no apunta nada. El driver va en el banco 0x0C, 8 KB vacíos: el juego lo pone en la ventana 0xA000 pero no lo lee nunca (medido en openMSX durante 5 minutos de demo y partida). Dentro de los 512 KB no hay 64 KB libres, así que el sector va detrás, en el banco relativo 0x40.
- **El texto:** el driver no puede pintar, porque la rutina de texto del juego cambia los bancos por encima de él. Deja el texto en RAM y el shim lo pinta con esa rutina en modo ASCII, como hace el juego con sus mensajes en inglés.
- **Probado** en openMSX como Yamanooto y metido en un pack de [nPackR](https://github.com/antxiko/msx-yamanooto-npackr) (v1.7.4, mapper `galious_enhanced`): grabar con objetos en un hueco sin tocar los otros, cerrar, reabrir y cargar, y vuelven los objetos. Todavía no se ha probado en un MSX real.

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
