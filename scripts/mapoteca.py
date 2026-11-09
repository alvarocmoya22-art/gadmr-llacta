"""El catalogo de la mapoteca, leido de las capas publicadas.

    python -I scripts/mapoteca.py

Escribe `datos/capas.json` y `datos/capas.js` con la ficha de cada capa que el
visor de territorio publica: cuantos registros tiene, que forma, que campos,
cuanto pesa, de cuando es y bajo que licencia esta.

NADA DE ESTO SE TRANSCRIBE. Los registros se cuentan abriendo el archivo, el
peso es el del archivo y la fecha es su fecha de modificacion. Una ficha de
catalogo escrita a mano envejece sin que nadie lo note: dice 212 barrios el dia
que ya son 214, y nadie vuelve a mirarla.

EL NOMBRE Y LA NOTA SI SON EDITORIALES, y se leen del catalogo de CHASKI
—`src/lib/municipio.ts`—, que es donde ya estaban. Asi hay un solo sitio donde
se describe una capa. Las capas publicadas que CHASKI no lista salen igual,
marcadas: que el visor publique algo que el analizador no ofrece es justo la
clase de hueco que una mapoteca existe para ensenar.

LA LICENCIA NO SE DEDUCE DEL ARCHIVO. Va declarada abajo, y lo que no esta
confirmado se marca para revisar en vez de afirmarlo. Lo derivado de
OpenStreetMap es ODbL y arrastra la licencia a lo que salga de ahi; decirlo mal
en un catalogo publico no es un detalle.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
VISOR = RAIZ.parent / "gadmr-visor-territorio"
DATOS = VISOR / "public" / "datos"
MUNICIPIO_TS = RAIZ.parent / "chaski" / "src" / "lib" / "municipio.ts"

URL_PUBLICA = "https://alvarocmoya22-art.github.io/gadmr-visor-territorio/datos"

# La licencia y el origen, declarados. `verificar` marca lo que esta deducido y
# alguien tiene que confirmar antes de que esto se publique de verdad.
ORIGEN = {
    "edificios.geojson":           ("OpenStreetMap", "ODbL", False),
    "red.json":                    ("OpenStreetMap", "ODbL", True),
    # Su campo `tipo` dice provincial (1.271) y estatal (13): es la red vial
    # del GAD Provincial, no OpenStreetMap. Estaba mal marcada aqui.
    "red_vial.geojson":            ("GAD Provincial de Chimborazo", "Por confirmar", True),
    "calles.json":                 ("OpenStreetMap", "ODbL", True),
    "manzanas.geojson":            ("INEC · Censo 2022", "Uso estadístico", False),
    "poblacion.json":              ("INEC · Censo 2022", "Derivado agregado", False),
    "barrios.geojson":             ("GADM Riobamba · INEC", "Municipal", False),
    "plataformas.geojson":         ("GADM Riobamba · INEC", "Municipal", False),
    "parroquias.geojson":          ("GADM Riobamba", "Municipal", False),
    "parroquias_canton.geojson":   ("GADM Riobamba · INEC", "Municipal", False),
    "clasificacion_suelo.geojson": ("GADM Riobamba · INEC", "Municipal", False),
    "limite_urbano.geojson":       ("GADM Riobamba", "Municipal", False),
    "equipamientos.geojson":       ("GADM Riobamba", "Municipal", False),
    "proyectos.geojson":           ("GADM Riobamba", "Municipal", False),
    "catastro.geojson":            ("GADM Riobamba", "Municipal · sin propietario", False),
}

# Lo que no se ofrece para descargar aunque este publicado: son piezas internas
# del visor, no capas. Se listan igual, dichas como lo que son.
AUXILIARES = {"poblacion.json", "calles.json"}


def log(m=""):
    print(str(m).encode("ascii", "replace").decode("ascii"), flush=True)


def catalogo_chaski() -> dict:
    """{archivo: (nombre, nota)} leido del catalogo de CHASKI."""
    if not MUNICIPIO_TS.exists():
        log(f"  AVISO: no esta {MUNICIPIO_TS}; las capas saldran sin nombre propio.")
        return {}
    texto = MUNICIPIO_TS.read_text(encoding="utf-8")
    fichas = {}
    for m in re.finditer(
        r'archivo:\s*"([^"]+)",\s*\n\s*nombre:\s*"([^"]+)",\s*\n\s*nota:\s*"([^"]+)"',
        texto,
    ):
        archivo, nombre, nota = m.groups()
        fichas[archivo] = (nombre, nota)
    return fichas


def describe(ruta: Path) -> dict:
    """Registros, forma y campos, abriendo el archivo."""
    try:
        dato = json.loads(ruta.read_text(encoding="utf-8"))
    except Exception as e:
        return {"error": f"no se pudo leer: {e}"}

    if isinstance(dato, dict) and dato.get("type") == "FeatureCollection":
        fs = dato.get("features", [])
        formas = sorted({f.get("geometry", {}).get("type") for f in fs if f.get("geometry")})
        campos = sorted({k for f in fs[:500] for k in (f.get("properties") or {})})
        return {"registros": len(fs), "formas": formas, "campos": campos}

    # red.json y poblacion.json no son GeoJSON: se describen por sus claves.
    if isinstance(dato, dict):
        detalle = {}
        for k, v in dato.items():
            if isinstance(v, (list, dict)):
                detalle[k] = len(v)
        return {"registros": None, "formas": [], "campos": sorted(dato.keys()),
                "detalle": detalle}
    return {"registros": len(dato) if isinstance(dato, list) else None,
            "formas": [], "campos": []}


def main() -> None:
    if not DATOS.exists():
        log(f"no existe {DATOS}")
        sys.exit(1)

    log("=== Mapoteca  ·  catalogo de las capas publicadas ===")
    fichas = catalogo_chaski()
    log(f"  catalogo de CHASKI: {len(fichas)} capas descritas")
    log()

    capas = []
    archivos = sorted(p for p in DATOS.iterdir() if p.suffix in (".geojson", ".json"))
    for ruta in archivos:
        d = describe(ruta)
        nombre, nota = fichas.get(ruta.name, (None, None))
        origen, licencia, verificar = ORIGEN.get(ruta.name, ("Por declarar", "Por declarar", True))
        capas.append({
            "archivo": ruta.name,
            "nombre": nombre or ruta.stem.replace("_", " ").capitalize(),
            "nota": nota,
            "en_chaski": ruta.name in fichas,
            "auxiliar": ruta.name in AUXILIARES,
            "registros": d.get("registros"),
            "formas": d.get("formas", []),
            "campos": d.get("campos", []),
            "detalle": d.get("detalle"),
            "bytes": ruta.stat().st_size,
            "modificado": datetime.fromtimestamp(
                ruta.stat().st_mtime, tz=timezone.utc
            ).date().isoformat(),
            "origen": origen,
            "licencia": licencia,
            "licencia_por_verificar": verificar,
            "descarga": f"{URL_PUBLICA}/{ruta.name}",
            "error": d.get("error"),
        })

    cuerpo = {
        "generado": datetime.now().date().isoformat(),
        "origen_publicado": URL_PUBLICA,
        "capas": capas,
    }
    destino = RAIZ / "datos"
    destino.mkdir(exist_ok=True)
    (destino / "capas.json").write_text(
        json.dumps(cuerpo, ensure_ascii=False, indent=2), encoding="utf-8")
    (destino / "capas.js").write_text(
        "/* Generado por scripts/mapoteca.py. No editar a mano. */\n"
        "window.LLACTA_CAPAS = " + json.dumps(cuerpo, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8")

    log(f"  {'archivo':<30} {'registros':>10} {'peso':>10}  {'licencia':<22} chaski")
    log(f"  {'-'*30} {'-'*10} {'-'*10}  {'-'*22} ------")
    for c in capas:
        reg = f"{c['registros']:,}" if c["registros"] is not None else "-"
        lic = c["licencia"] + (" ?" if c["licencia_por_verificar"] else "")
        log(f"  {c['archivo']:<30} {reg:>10} {c['bytes']/1024:>9,.0f}K  "
            f"{lic:<22} {'si' if c['en_chaski'] else 'NO'}")

    fuera = [c["archivo"] for c in capas if not c["en_chaski"] and not c["auxiliar"]]
    dudosas = [c["archivo"] for c in capas if c["licencia_por_verificar"]]
    log()
    log(f"  capas publicadas: {len(capas)}  ·  "
        f"{sum(c['bytes'] for c in capas)/1024/1024:,.1f} MB en total")
    if fuera:
        log(f"  publicadas pero NO en el catalogo de CHASKI: {', '.join(fuera)}")
    if dudosas:
        log(f"  licencia por verificar: {', '.join(dudosas)}")
    log()
    log(f"  {destino / 'capas.json'}")
    log("listo")


if __name__ == "__main__":
    main()
