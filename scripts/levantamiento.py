"""De donde viene cada dato del observatorio, y que tan completo esta.

    python -I scripts/levantamiento.py

Escribe `datos/levantamiento.json` · `.js`: cada capa agrupada por su fuente,
con cuantos registros trae y que parte de cada campo esta realmente relleno.

QUE ES ESTA VENTANA. El observatorio cruza datos de cuatro origenes muy
distintos —OpenStreetMap, el inventario municipal, la red provincial y el
Censo del INEC— y hasta ahora eso solo se veia en letra chica al pie de una
cifra. Aqui se ve entero: que trae cada fuente, bajo que licencia, y donde
esta incompleto.

NO ES LA MAPOTECA. La mapoteca contesta «que capas hay y como las descargo».
Esta contesta «de donde salio esto y cuanto me puedo fiar», que es otra
pregunta y la contesta el que levanta la informacion, no el que la consume.

EL RELLENO SE CUENTA, NO SE DECLARA. Para cada campo se mira cuantos registros
lo traen de verdad: vacio, nulo y la cadena vacia no cuentan. Un campo que
existe en el esquema y esta vacio en el 40 % de las filas es un campo que
todavia no esta levantado, y decir «tiene rodadura» sin esa cifra al lado es
decir media verdad.

LO QUE TODAVIA NO PUEDE CONTESTAR. Cuanto avanzo el levantamiento esta semana,
quien toco que y cuando. Eso necesita historico —la base de datos del encargo—
porque hoy cada archivo es una foto sin antes.
"""
import json
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
DATOS = RAIZ.parent / "gadmr-visor-territorio" / "public" / "datos"

# De donde se descargan de verdad. No se copia ni un archivo a este
# repositorio: el visor ya las publica con el CORS abierto, asi que el boton
# de descarga apunta al original. Copiarlas aqui significaria tener dos
# versiones que se separan en cuanto el visor actualice una.
URL_PUBLICA = "https://alvarocmoya22-art.github.io/gadmr-visor-territorio/datos"

# De donde viene cada cosa. Va declarado: no se deduce del archivo, y lo que
# no esta confirmado se marca para que alguien lo confirme.
FUENTES = [
    {
        "clave": "osm",
        "nombre": "OpenStreetMap",
        "licencia": "ODbL",
        "nota": "Lo levanta cualquiera, y el municipio levanta en campo con Every Door, "
                "que escribe directo a OSM. Una base derivada de esto es tambien ODbL.",
        "capas": ["edificios.geojson", "red.json", "calles.json"],
    },
    {
        "clave": "gadm",
        "nombre": "GADM Riobamba",
        "licencia": "Municipal",
        "nota": "El inventario propio: lo que el municipio levanto y mantiene.",
        "capas": ["equipamientos.geojson", "proyectos.geojson", "catastro.geojson",
                  "barrios.geojson", "plataformas.geojson", "limite_urbano.geojson",
                  "parroquias.geojson", "parroquias_canton.geojson",
                  "clasificacion_suelo.geojson"],
    },
    {
        "clave": "provincial",
        "nombre": "GAD Provincial de Chimborazo",
        "licencia": "Por confirmar",
        "nota": "La red vial provincial y estatal, con su capa de rodadura. "
                "Estaba marcada como OpenStreetMap en la mapoteca y no lo es: "
                "su campo `tipo` dice provincial y estatal.",
        "verificar": True,
        "capas": ["red_vial.geojson"],
    },
    {
        "clave": "inec",
        "nombre": "INEC · Censo 2022",
        "licencia": "Derivado agregado",
        "nota": "Las manzanas y la poblacion. La capa de sectores no se publica: "
                "sus condiciones de uso son de copyright.",
        "capas": ["manzanas.geojson", "poblacion.json"],
    },
]

# Campos que conviene mirar de cerca, porque de su relleno cuelga un indicador.
CLAVE = {
    "red_vial.geojson": ["rodadura", "nombre"],
    "edificios.geojson": ["altura", "medido"],
    "equipamientos.geojson": ["tipologia", "estado", "elemento"],
    "manzanas.geojson": ["poblacion", "viviendas"],
}

VACIOS = {None, "", "nan", "None", "SIN DATO", "No encontrado", "-"}


def log(m=""):
    print(str(m).encode("ascii", "replace").decode("ascii"), flush=True)


def leer(ruta: Path):
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except Exception as e:
        return {"_error": str(e)}


def mirar(ruta: Path) -> dict:
    """Registros, campos y que parte de cada campo esta relleno de verdad."""
    d = leer(ruta)
    ficha = {
        "archivo": ruta.name,
        "descarga": f"{URL_PUBLICA}/{ruta.name}",
        "bytes": ruta.stat().st_size,
        "modificado": datetime.fromtimestamp(
            ruta.stat().st_mtime, tz=timezone.utc).date().isoformat(),
    }
    if isinstance(d, dict) and "_error" in d:
        ficha["error"] = d["_error"]
        return ficha

    if isinstance(d, dict) and d.get("type") == "FeatureCollection":
        fs = d.get("features", [])
        ficha["registros"] = len(fs)
        campos = []
        nombres = sorted({k for f in fs[:1000] for k in (f.get("properties") or {})})
        for k in nombres:
            con = sum(
                1 for f in fs
                if str((f.get("properties") or {}).get(k)).strip() not in VACIOS
            )
            campos.append({
                "nombre": k,
                "con_dato": con,
                "pct": round(con / len(fs) * 100, 1) if fs else 0.0,
                "clave": k in CLAVE.get(ruta.name, []),
            })
        ficha["campos"] = campos
        ficha["formas"] = sorted({
            f["geometry"]["type"] for f in fs if f.get("geometry")
        })
        return ficha

    # Lo que no es GeoJSON se describe por sus claves.
    if isinstance(d, dict):
        ficha["registros"] = None
        ficha["detalle"] = {
            k: (len(v) if hasattr(v, "__len__") else v)
            for k, v in d.items() if not isinstance(v, (int, float))
        }
        for k, v in d.items():
            if isinstance(v, list) and v:
                ficha["registros"] = len(v)
                break
    return ficha


def rodadura() -> dict | None:
    """El desglose de la capa de rodadura, en kilometros.

    Es el dato del que cuelga el indicador 6 del observatorio —«gente en calle
    sin capa de rodadura»— y lo primero que ensena no es cuantas calles estan
    sin asfaltar: es cuantas no tienen el dato."""
    ruta = DATOS / "red_vial.geojson"
    if not ruta.exists():
        return None
    fs = leer(ruta).get("features", [])
    km, n = Counter(), Counter()
    for f in fs:
        p = f.get("properties") or {}
        r = (p.get("rodadura") or "SIN DATO").strip() or "SIN DATO"
        km[r] += float(p.get("km") or 0)
        n[r] += 1
    total = sum(km.values())
    return {
        "total_km": round(total, 1),
        "total_tramos": len(fs),
        "clases": [
            {"clase": r.capitalize() if r != "SIN DATO" else "Sin dato",
             "tramos": n[r], "km": round(v, 1),
             "pct": round(v / total * 100, 1) if total else 0.0,
             "sin_dato": r == "SIN DATO"}
            for r, v in km.most_common()
        ],
    }


def main() -> None:
    hoy = date.today().isoformat()
    log("=== LLACTA  ·  de donde viene cada dato ===")
    log()

    fuentes = []
    for f in FUENTES:
        capas = []
        for nombre in f["capas"]:
            ruta = DATOS / nombre
            if not ruta.exists():
                log(f"  FALTA {nombre}")
                continue
            capas.append(mirar(ruta))
        if not capas:
            continue
        fuentes.append({**{k: v for k, v in f.items() if k != "capas"}, "capas": capas})

        log(f"  === {f['nombre']}  ·  {f['licencia']}"
            + ("  (POR CONFIRMAR)" if f.get("verificar") else "") + " ===")
        for c in capas:
            reg = f"{c['registros']:,}" if c.get("registros") else "-"
            log(f"    {c['archivo']:<28} {reg:>9} reg  {c['bytes']/1024:>8,.0f} KB"
                f"  {c['modificado']}")
            for campo in c.get("campos", []):
                if campo["clave"] or campo["pct"] < 95:
                    marca = " <<" if campo["clave"] else ""
                    log(f"        {campo['nombre']:<18} relleno {campo['pct']:>5.1f} %"
                        f"  ({campo['con_dato']:,}){marca}")
        log()

    rod = rodadura()
    if rod:
        log("  === Capa de rodadura, en kilometros ===")
        for c in rod["clases"]:
            log(f"    {c['clase']:<14} {c['tramos']:>5} tramos  {c['km']:>8,.1f} km"
                f"  ({c['pct']:4.1f} %)" + ("   <- el hueco" if c["sin_dato"] else ""))
        log(f"    {'TOTAL':<14} {rod['total_tramos']:>5} tramos  "
            f"{rod['total_km']:>8,.1f} km")
        log()

    cuerpo = {"generado": hoy, "origen_publicado": URL_PUBLICA,
              "fuentes": fuentes, "rodadura": rod}
    destino = RAIZ / "datos"
    destino.mkdir(exist_ok=True)
    (destino / "levantamiento.json").write_text(
        json.dumps(cuerpo, ensure_ascii=False, indent=2), encoding="utf-8")
    (destino / "levantamiento.js").write_text(
        "/* Generado por scripts/levantamiento.py. No editar a mano. */\n"
        "window.LLACTA_LEV = " + json.dumps(cuerpo, ensure_ascii=False) + ";\n",
        encoding="utf-8")
    log(f"  {destino / 'levantamiento.json'}")
    log("listo")


if __name__ == "__main__":
    main()
