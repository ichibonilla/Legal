#!/usr/bin/env python3
"""Registro único de un calendario de difusión: validar, generar, cotejar, cerrar.

Uso:
  python3 herramientas/difusion.py validar  [--proyecto difusion/red-psicologos]
  python3 herramientas/difusion.py generar  [--proyecto ...] [--sin-tarjetas]
  python3 herramientas/difusion.py cotejo   [FECHA] [--dias 30] [--estricto] [--proyecto ...]
  python3 herramientas/difusion.py cerrar   [--proyecto ...]

La única fuente es <proyecto>/registro.json. Todo lo que está en
<proyecto>/generados/ (calendario, piezas listas para copiar, lote, tarjetas,
pendientes, handoff) se sobrescribe en cada `generar`; no se edita a mano.

Dos tipos de registro:
  estudios (S-xxx): la fuente científica y los hallazgos cotejados contra ella.
  piezas   (P-xxx): el mensaje para el grupo, con fecha de publicación y los
                    estudios que cita.

`folio` en un estudio es la página o tabla del texto completo donde consta
cada cifra; queda vacío mientras el cotejo se haya hecho solo contra el
resumen. `cotejo --estricto` lo exige.
"""
import argparse
import json
import re
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

ESTADOS = ("VERIFICADO", "POR VERIFICAR", "PENDIENTE")
COMUNES = ("id", "estado", "verificado_el", "supersede", "razon")
CAMPOS_ESTUDIO = COMUNES + ("cita", "doi", "pmid", "diseno", "hallazgos", "fuente", "folio")
CAMPOS_PIEZA = COMUNES + ("fecha", "titulo", "cuerpo", "estudios", "tarjeta")
FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PALABRAS = (75, 105)  # margen alrededor de las ~90 palabras del cuerpo

PALETA = {"fondo": "#131237", "medio": "#2F2E47", "acento": "#5C6684",
          "claro": "#D1D0CB", "blanco": "#FFFFFF"}


def cargar(proyecto):
    with open(Path(proyecto) / "registro.json", encoding="utf-8") as f:
        return json.load(f)


def superados(lista):
    return {r["supersede"]: r["id"] for r in lista if r.get("supersede")}


def vigentes(lista):
    sup = superados(lista)
    return [r for r in lista if r["id"] not in sup]


def palabras(texto):
    limpio = re.sub(r"[*_~]", "", texto)
    return len([w for w in re.split(r"\s+", limpio) if re.search(r"\w", w)])


def validar(d):
    errores = []
    p = d["proyecto"]
    for c in ("nombre", "enlace", "frecuencia_dias", "hora", "actualizado_el", "excluir"):
        if c not in p:
            errores.append(f"proyecto: falta el campo «{c}».")
    for grupo, campos in (("estudios", CAMPOS_ESTUDIO), ("piezas", CAMPOS_PIEZA)):
        lista = d.get(grupo, [])
        ids = [r.get("id") for r in lista]
        vistos, reemplazados = set(), {}
        for r in lista:
            rid = r.get("id", "?")
            for c in campos:
                if c not in r:
                    errores.append(f"{rid}: falta el campo «{c}».")
            if rid in vistos:
                errores.append(f"{rid}: identificador duplicado.")
            vistos.add(rid)
            if r.get("estado") not in ESTADOS:
                errores.append(f"{rid}: estado no válido «{r.get('estado')}».")
            if r.get("estado") == "VERIFICADO" and not FECHA.match(r.get("verificado_el") or ""):
                errores.append(f"{rid}: VERIFICADO sin fecha válida en verificado_el.")
            s = r.get("supersede")
            if s:
                if not r.get("razon"):
                    errores.append(f"{rid}: reemplaza a {s} sin indicar razón.")
                if s not in ids:
                    errores.append(f"{rid}: supersede apunta a {s}, que no existe.")
                if s == rid:
                    errores.append(f"{rid}: se reemplaza a sí mismo.")
                if s in reemplazados:
                    errores.append(f"{s}: reemplazado dos veces ({reemplazados[s]} y {rid}).")
                reemplazados[s] = rid
    ids_est = {r["id"] for r in d.get("estudios", [])}
    for r in d.get("piezas", []):
        if not FECHA.match(r.get("fecha") or ""):
            errores.append(f"{r['id']}: fecha de publicación no válida.")
        for s in r.get("estudios", []):
            if s not in ids_est:
                errores.append(f"{r['id']}: cita {s}, que no existe.")
    return errores


def ensamblar(pieza, d):
    """Texto final de la pieza, listo para pegar en WhatsApp."""
    p = d["proyecto"]
    est = {r["id"]: r for r in d["estudios"]}
    citas = []
    for s in pieza["estudios"]:
        e = est[s]
        citas.append(f"{e['cita']} https://doi.org/{e['doi']}")
    fuente = "📚 *Fuente:* " if len(citas) == 1 else "📚 *Fuentes:*\n"
    bloques = [f"📊 *{pieza['titulo']}*", pieza["cuerpo"].strip(),
               fuente + "\n".join(citas),
               f"{p['cierre']}\n🔗 {p['enlace']}"]
    return "\n\n".join(bloques) + "\n"


def problemas_pieza(pieza, d, estricto=False):
    p = d["proyecto"]
    est = {r["id"]: r for r in d["estudios"]}
    sup_est = superados(d["estudios"])
    obs = []
    if pieza["estado"] != "VERIFICADO":
        obs.append(f"pieza {pieza['estado']}. {pieza['razon']}".strip())
    for s in pieza["estudios"]:
        e = est.get(s)
        if not e:
            obs.append(f"{s}: no existe en el registro.")
            continue
        if s in sup_est:
            obs.append(f"{s}: superado por {sup_est[s]}; actualizar la cita.")
            continue
        if e["estado"] != "VERIFICADO":
            obs.append(f"{s}: {e['estado']}. {e['razon']}".strip())
        if not e.get("doi"):
            obs.append(f"{s}: sin DOI.")
        if estricto and not e.get("folio"):
            obs.append(f"{s}: sin folio (página o tabla del texto completo).")
    n = palabras(pieza["cuerpo"])
    if not PALABRAS[0] <= n <= PALABRAS[1]:
        obs.append(f"cuerpo de {n} palabras (margen {PALABRAS[0]}–{PALABRAS[1]}).")
    texto = ensamblar(pieza, d) if not obs or all("no existe" not in o for o in obs) else ""
    for termino in p.get("excluir", []):
        if termino.lower() in texto.lower():
            obs.append(f"menciona «{termino}», que no corresponde en este canal.")
    if texto and p["enlace"] not in texto:
        obs.append("falta el enlace del grupo.")
    return obs


def ventana(d, desde, dias):
    hasta = desde + timedelta(days=dias)
    return [r for r in vigentes(d["piezas"])
            if desde.isoformat() <= r["fecha"] <= hasta.isoformat()]


# ---------------------------------------------------------------- tarjetas

FUENTES_SERIF = [
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "C:/Windows/Fonts/georgia.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
]
FUENTES_SANS = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def _fuente(ImageFont, rutas, tam):
    for r in rutas:
        if Path(r).exists():
            return ImageFont.truetype(r, tam)
    return ImageFont.load_default()


def _envolver(draw, texto, fuente, ancho):
    lineas, actual = [], ""
    for w in texto.split():
        prueba = f"{actual} {w}".strip()
        if draw.textlength(prueba, font=fuente) <= ancho:
            actual = prueba
        else:
            lineas.append(actual)
            actual = w
    if actual:
        lineas.append(actual)
    return lineas


def tarjetas(d, carpeta):
    """Una imagen cuadrada por pieza vigente, en la paleta, sin marca institucional."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None
    carpeta.mkdir(parents=True, exist_ok=True)
    est = {r["id"]: r for r in d["estudios"]}
    L, M = 1080, 96
    serif_g = _fuente(ImageFont, FUENTES_SERIF, 150)
    serif_m = _fuente(ImageFont, FUENTES_SERIF, 50)
    sans_s = _fuente(ImageFont, FUENTES_SANS, 28)
    sans_xs = _fuente(ImageFont, FUENTES_SANS, 26)
    hechas = []
    for r in vigentes(d["piezas"]):
        t = r["tarjeta"]
        img = Image.new("RGB", (L, L), PALETA["fondo"])
        dr = ImageDraw.Draw(img)
        dr.rectangle([0, L - 150, L, L], fill=PALETA["medio"])
        dr.text((M, M), t["rotulo"].upper(), font=sans_s, fill=PALETA["claro"])
        dr.line([M, M + 56, M + 120, M + 56], fill=PALETA["acento"], width=4)
        tam, cifra_f = 150, serif_g
        while dr.textlength(t["cifra"], font=cifra_f) > L - 2 * M and tam > 60:
            tam -= 10
            cifra_f = _fuente(ImageFont, FUENTES_SERIF, tam)
        y = 300
        dr.text((M, y), t["cifra"], font=cifra_f, fill=PALETA["blanco"])
        y += 200
        for linea in _envolver(dr, t["frase"], serif_m, L - 2 * M)[:4]:
            dr.text((M, y), linea, font=serif_m, fill=PALETA["blanco"])
            y += 66
        cortas = [est[s]["referencia_corta"] for s in r["estudios"] if s in est]
        ref = " · ".join(cortas)
        if dr.textlength(ref, font=sans_xs) > L - 2 * M:  # varias fuentes: solo autor y año
            ref = " · ".join(c.split("),")[0] + ")" for c in cortas)
        dr.text((M, L - 112), ref, font=sans_xs, fill=PALETA["claro"])
        dr.text((M, L - 68), d["proyecto"]["nombre"], font=sans_xs, fill=PALETA["claro"])
        nombre = f"{r['fecha']}_{r['id']}.png"
        img.save(carpeta / nombre, optimize=True)
        hechas.append(nombre)
    return hechas


# ---------------------------------------------------------------- generar

def generar(d, proyecto, con_tarjetas=True):
    out = Path(proyecto) / "generados"
    piezas_dir = out / "piezas"
    if piezas_dir.exists():
        shutil.rmtree(piezas_dir)
    piezas_dir.mkdir(parents=True)
    p = d["proyecto"]
    hoy = date.today()
    cab = (f"<!-- Generado por herramientas/difusion.py el {hoy.isoformat()} a partir de "
           f"registro.json. No editar a mano: los cambios se hacen en registro.json y se regenera. -->\n\n")
    est = {r["id"]: r for r in d["estudios"]}
    sup_p, sup_e = superados(d["piezas"]), superados(d["estudios"])
    vig = sorted(vigentes(d["piezas"]), key=lambda r: (r["fecha"], r["id"]))

    # Piezas listas para copiar, una por archivo
    for r in vig:
        (piezas_dir / f"{r['fecha']}_{r['id']}.txt").write_text(ensamblar(r, d), encoding="utf-8")

    # Lote de los próximos 30 días
    lote = ventana(d, hoy, 30)
    lineas = [cab, f"# Lote — {p['nombre']}\n",
              f"Piezas del {hoy.isoformat()} al {(hoy + timedelta(days=30)).isoformat()}, "
              f"cada {p['frecuencia_dias']} días, a las {p['hora']}. "
              f"Cada bloque se copia tal cual; la tarjeta está en `generados/tarjetas/`.\n"]
    for r in lote:
        obs = problemas_pieza(r, d)
        lineas.append(f"---\n\n## {r['fecha']} · {r['id']}\n")
        lineas.append("> Antes de publicar: " + " ".join(obs) + "\n" if obs else "> Lista para publicar.\n")
        lineas.append("```\n" + ensamblar(r, d) + "```\n")
    (out / "lote.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    # Calendario
    lineas = [cab, f"# Calendario — {p['nombre']}\n",
              f"Registro actualizado el {p['actualizado_el']}. Frecuencia: cada {p['frecuencia_dias']} días, "
              f"{p['hora']}.\n", "| Fecha | Pieza | Estado | Tema | Estudios | Palabras |",
              "|---|---|---|---|---|---|"]
    for r in sorted(d["piezas"], key=lambda r: (r["fecha"], r["id"])):
        ident = f"~~{r['id']}~~ (superada por {sup_p[r['id']]})" if r["id"] in sup_p else r["id"]
        estudios = ", ".join(f"{s} ({est[s]['estado']})" if s in est else s for s in r["estudios"])
        lineas.append(f"| {r['fecha']} | {ident} | {r['estado']} | {r['titulo'].replace('|', '/')} | "
                      f"{estudios} | {palabras(r['cuerpo'])} |")
    (out / "calendario.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    # Pendientes
    ev = vigentes(d["estudios"])
    lineas = [cab, "# Pendientes y por verificar\n"]
    for estado in ("PENDIENTE", "POR VERIFICAR"):
        filas = [r for r in ev + vig if r["estado"] == estado]
        lineas.append(f"## {estado} ({len(filas)})\n")
        lineas += [f"- **{r['id']}** — {r.get('titulo') or r.get('referencia_corta')}. {r['razon']}"
                   for r in filas]
        lineas.append("")
    sin_folio = [r for r in ev if not r["folio"]]
    lineas.append(f"## Sin folio ({len(sin_folio)} de {len(ev)} estudios vigentes)\n")
    lineas.append("Cotejados contra el resumen publicado. El folio (página o tabla del texto completo) "
                  "se completa al leer el artículo; `cotejo --estricto` lo exige.")
    (out / "pendientes.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    # Handoff
    ultima = vig[-1]["fecha"] if vig else "—"
    objetivo = (hoy + timedelta(days=30)).isoformat()
    lineas = [cab, f"# Handoff — {p['nombre']}\n",
              f"Estado al {p['actualizado_el']}. Fuente única: `registro.json`.\n",
              "## Encuadre\n"]
    lineas += [f"- {x}" for x in p.get("reglas", [])]
    lineas.append(f"\n## Cobertura\n\nÚltima pieza programada: {ultima}. "
                  f"Objetivo de antelación (30 días): {objetivo}. "
                  + ("Cubierto." if ultima != "—" and ultima >= objetivo else
                     "Falta preparar piezas hasta esa fecha."))
    proximas = [r for r in vig if r["fecha"] >= hoy.isoformat()][:3]
    lineas.append("\n## Próximas publicaciones\n")
    lineas += [f"- {r['fecha']} — {r['id']}: {r['titulo']}" for r in proximas]
    lineas.append("\n## Estudios del registro\n")
    for e in d["estudios"]:
        marca = f" (superado por {sup_e[e['id']]})" if e["id"] in sup_e else ""
        lineas.append(f"- **{e['id']}**{marca} — {e['estado']} — {e['cita']} https://doi.org/{e['doi']}")
    sup = [r for r in d["estudios"] + d["piezas"] if r.get("supersede")]
    if sup:
        lineas.append("\n## Registros reemplazados\n")
        lineas += [f"- {r['supersede']} → {r['id']} ({r['verificado_el'] or 'sin fecha'}): {r['razon']}"
                   for r in sup]
    (out / "handoff.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    archivos = ["lote.md", "calendario.md", "pendientes.md", "handoff.md", f"piezas/ ({len(vig)})"]
    if con_tarjetas:
        t_dir = out / "tarjetas"
        if t_dir.exists():
            shutil.rmtree(t_dir)
        hechas = tarjetas(d, t_dir)
        archivos.append(f"tarjetas/ ({len(hechas)})" if hechas is not None
                        else "tarjetas omitidas: instalar Pillow (pip install pillow)")
    return archivos


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accion", choices=["validar", "generar", "cotejo", "cerrar"])
    ap.add_argument("fecha", nargs="?", help="en cotejo: desde qué fecha (AAAA-MM-DD); por defecto, hoy")
    ap.add_argument("--proyecto", default="difusion/red-psicologos")
    ap.add_argument("--dias", type=int, default=30, help="en cotejo: días a revisar (por defecto 30)")
    ap.add_argument("--estricto", action="store_true", help="en cotejo: exige folio en cada estudio citado")
    ap.add_argument("--sin-tarjetas", action="store_true", help="no regenera las imágenes")
    a = ap.parse_args()
    d = cargar(a.proyecto)

    errores = validar(d)
    if errores:
        print("El registro tiene errores:")
        for e in errores:
            print(f"  - {e}")
        return 1

    if a.accion == "cotejo":
        desde = date.fromisoformat(a.fecha) if a.fecha else date.today()
        piezas = ventana(d, desde, a.dias)
        print(f"Cotejo del {desde.isoformat()} al {(desde + timedelta(days=a.dias)).isoformat()}: "
              f"{len(piezas)} piezas.")
        total = 0
        for r in piezas:
            obs = problemas_pieza(r, d, a.estricto)
            if obs:
                total += len(obs)
                print(f"  {r['fecha']} {r['id']}:")
                for o in obs:
                    print(f"    - {o}")
        if not total:
            print("Sin observaciones: todo lo citado está VERIFICADO y vigente.")
            return 0
        print(f"{total} observaciones. Esas piezas no salen hasta resolverlas o retirar la cita.")
        return 1

    if a.accion == "validar":
        print(f"Registro válido: {len(d['estudios'])} estudios, {len(d['piezas'])} piezas.")
        return 0

    archivos = generar(d, a.proyecto, con_tarjetas=not a.sin_tarjetas)
    print("Generados: " + ", ".join(archivos))
    if a.accion == "cerrar":
        for grupo in ("estudios", "piezas"):
            vig = vigentes(d[grupo])
            cuenta = ", ".join(f"{e}: {sum(1 for r in vig if r['estado'] == e)}" for e in ESTADOS)
            print(f"{grupo.capitalize()} vigentes: {len(vig)} ({cuenta}); "
                  f"superados: {len(superados(d[grupo]))}.")
        vig = sorted(vigentes(d["piezas"]), key=lambda r: r["fecha"])
        objetivo = (date.today() + timedelta(days=30)).isoformat()
        if not vig or vig[-1]["fecha"] < objetivo:
            print(f"Aviso: la programación no cubre los próximos 30 días (hasta {objetivo}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
