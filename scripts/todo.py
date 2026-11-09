"""Rehace todo el observatorio, en orden, y sella las paginas.

    python -I scripts/todo.py

Corre los cinco pasos en el unico orden en que tienen sentido —cada uno
necesita lo que dejo el anterior— y al final pone el sello de version en las
paginas.

POR QUE EL SELLO. Un navegador que ya visito la pagina se guarda
`datos/escalas.js` en su cache y lo vuelve a usar sin preguntar. Publicar un
calculo nuevo no basta: quien ya entro veria la fecha nueva de la cabecera
—que viene del HTML, que si se revalida— con las cifras viejas al lado. En un
tablero cualquiera eso es una molestia; en un observatorio es publicar una
cifra equivocada con una fecha que la respalda.

El sello es la fecha de modificacion de cada archivo pegada a su enlace
—`datos/escalas.js?v=1794...`—. Si el archivo no cambio, la direccion es la
misma y el navegador reutiliza lo que tiene, que es lo que se quiere. Si
cambio, la direccion es otra y no hay cache que valga.

No es un numero escrito a mano que alguien tenga que acordarse de subir: sale
del propio archivo.
"""
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent

PASOS = [
    ("indicadores.py", "los tres indicadores del canton"),
    ("comprobar_indicadores.py", "la comprobacion por otros dos caminos"),
    ("escalas.py", "plataformas, parroquias y el mapa de manzanas"),
    ("red_cercania.py", "la red vial por cercania"),
    ("mapoteca.py", "el catalogo de capas publicadas"),
    ("levantamiento.py", "de donde viene cada dato y cuanto falta"),
]

PAGINAS = ["index.html", "mapoteca.html", "levantamiento.html"]


def log(m=""):
    print(str(m).encode("ascii", "replace").decode("ascii"), flush=True)


def sellar() -> int:
    """Pone `?v=<mtime>` en cada enlace local de las paginas. Devuelve cuantos."""
    patron = re.compile(r'(src|href)="([^":]+?\.(?:js|css))(\?v=\d+)?"')
    tocados = 0
    for nombre in PAGINAS:
        pagina = RAIZ / nombre
        if not pagina.exists():
            continue
        texto = pagina.read_text(encoding="utf-8")

        def sello(m):
            nonlocal tocados
            attr, ruta = m.group(1), m.group(2)
            archivo = RAIZ / ruta
            if not archivo.exists():
                return m.group(0)
            tocados += 1
            return f'{attr}="{ruta}?v={int(archivo.stat().st_mtime)}"'

        nuevo = patron.sub(sello, texto)
        if nuevo != texto:
            pagina.write_text(nuevo, encoding="utf-8")
    return tocados


def main() -> None:
    log("=== LLACTA  ·  rehacer todo ===")
    log()
    for archivo, que in PASOS:
        ruta = AQUI / archivo
        if not ruta.exists():
            log(f"  FALTA {archivo}; se salta.")
            continue
        log(f"--- {archivo}  ·  {que}")
        r = subprocess.run([sys.executable, "-I", str(ruta)], cwd=RAIZ)
        if r.returncode != 0:
            log(f"\n  {archivo} fallo con codigo {r.returncode}. Se detiene aqui:")
            log("  seguir dejaria las paginas con datos a medias.")
            sys.exit(r.returncode)
        log()

    n = sellar()
    log(f"--- sello de version en {n} enlaces de {len(PAGINAS)} paginas")
    log()
    log("listo. Revisa la pagina antes de hacer commit.")


if __name__ == "__main__":
    main()
