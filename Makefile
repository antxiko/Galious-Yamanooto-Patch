# Partidas en la flash del Yamanooto. La ROM no se distribuye: va en la raiz
# como galious.rom (sha256 en tools/juego.py).

ROM = galious.rom

all: test

# los .bin de launcher/ desde sus .asm (pasmo en el PATH)
bins:
	python3 tools/bins.py

# la imagen de 2 MB para grabar en el cartucho
imagen: $(ROM)
	python3 tools/imagen.py $(ROM)

# la web: el README en docs/ (ingles) y docs/es/ (castellano)
web:
	python3 tools/web.py

test:
	python3 -m unittest discover -s tests -v

.PHONY: all bins imagen web test
