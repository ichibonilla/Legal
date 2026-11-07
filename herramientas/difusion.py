#!/usr/bin/env python3
"""Registro único de un calendario de difusión: validar, generar, cotejar, medir, cerrar.

Uso:
  python3 herramientas/difusion.py validar  [--proyecto difusion/red-psicologos]
  python3 herramientas/difusion.py generar  [--proyecto ...] [--sin-tarjetas] [--desde AAAA-MM-DD]
  python3 herramientas/difusion.py cotejo   [FECHA] [--dias 30] [--estricto] [--proyecto ...]
  python3 herramientas/difusion.py metricas P-xxx --miembros N --leidos N --reacciones N
                                            --respuestas N --nuevos N [--publicada "AAAA-MM-DD HH:MM"]
  python3 herramientas/difusion.py horarios [--proyecto ...]
  python3 herramientas/difusion.py cerrar   [--proyecto ...]

La única fuente es <proyecto>/registro.json. Todo lo que está en
<proyecto>/generados/ (lote, piezas, tarjetas, calendario, horarios,
pendientes, handoff) se sobrescribe en cada `generar`; no se edita a mano.

Dos tipos de registro:
  estudios (S-xxx): la fuente científica, su región y los hallazgos cotejados.
  piezas   (P-xxx): el mensaje para el grupo, con fecha, hora de prueba,
                    estudios que cita y, una vez publicado, sus métricas.

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
CAMPOS_ESTUDIO = COMUNES + ("cita", "cita_breve", "doi", "pmid", "diseno", "tipo_evidencia", "region", "paises",
                            "hallazgos", "fuente", "folio")
CAMPOS_PIEZA = COMUNES + ("fecha", "hora", "titulo", "estudios", "tarjeta")
SECCIONES = ("gancho", "introduccion", "desarrollo", "conclusion")
GANCHO_MAX = 110      # lo que se alcanza a leer en la vista previa de la notificación
CAMPOS_METRICAS = ("miembros", "leidos", "reacciones", "respuestas", "nuevos")
FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HORA = re.compile(r"^\d{2}:\d{2}$")
PALABRAS = (65, 100)   # cuerpo de unas 75 a 90 palabras; 10 menos por cada fuente adicional
TITULO_MAX = 60        # lo que se alcanza a leer en la notificación

PALETA = {"fondo": "#131237", "medio": "#2F2E47", "acento": "#5C6684",
          "claro": "#D1D0CB", "blanco": "#FFFFFF"}


def cargar(proyecto):
    with open(Path(proyecto) / "registro.json", encoding="utf-8") as f:
        return json.load(f)


def guardar(d, proyecto):
    with open(Path(proyecto) / "registro.json", "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write("\n")


def superados(lista):
    return {r["supersede"]: r["id"] for r in lista if r.get("supersede")}


def vigentes(lista):
    sup = superados(lista)
    return [r for r in lista if r["id"] not in sup]


def cuerpo(pieza):
    """Texto entre el título y la fuente. Las piezas nuevas se escriben por secciones
    (gancho, introducción, desarrollo, conclusión); las anteriores, en un solo `cuerpo`."""
    if pieza.get("secciones"):
        s = pieza["secciones"]
        return "\n\n".join(s[k].strip() for k in SECCIONES[1:])
    return pieza["cuerpo"].strip()


def palabras(texto):
    limpio = re.sub(r"[*_~]", "", texto)
    return len([w for w in re.split(r"\s+", limpio) if re.search(r"\w", w)])


# ---------------------------------------------------------------- validar

def validar(d):
    errores = []
    p = d["proyecto"]
    for c in ("nombre", "enlace", "cierre", "frecuencia_dias", "franjas", "ventana_horaria",
              "limite_caracteres", "regiones", "tipos_evidencia", "ocde", "actualizado_el", "excluir"):
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
    for e in d.get("estudios", []):
        if e.get("region") not in p.get("regiones", []):
            errores.append(f"{e['id']}: región «{e.get('region')}» fuera de las admitidas.")
        if e.get("tipo_evidencia") not in p.get("tipos_evidencia", []):
            errores.append(f"{e['id']}: tipo de evidencia «{e.get('tipo_evidencia')}» fuera de los admitidos.")
        if not e.get("paises"):
            errores.append(f"{e['id']}: sin países de afiliación.")
    ids_est = {r["id"] for r in d.get("estudios", [])}
    ini, fin = p.get("ventana_horaria", ["00:00", "23:59"])
    for r in d.get("piezas", []):
        if not FECHA.match(r.get("fecha") or ""):
            errores.append(f"{r['id']}: fecha de publicación no válida.")
        h = r.get("hora") or ""
        if not HORA.match(h):
            errores.append(f"{r['id']}: hora no válida «{h}».")
        elif r["id"] not in superados(d["piezas"]) and not ini <= h <= fin:
            errores.append(f"{r['id']}: hora {h} fuera de la ventana {ini}–{fin}.")
        if r.get("secciones"):
            faltan = [k for k in SECCIONES if not (r["secciones"].get(k) or "").strip()]
            if faltan:
                errores.append(f"{r['id']}: secciones vacías: {', '.join(faltan)}.")
        elif not (r.get("cuerpo") or "").strip():
            errores.append(f"{r['id']}: sin cuerpo ni secciones.")
        for s in r.get("estudios", []):
            if s not in ids_est:
                errores.append(f"{r['id']}: cita {s}, que no existe.")
        m = r.get("metricas")
        if m:
            for c in CAMPOS_METRICAS:
                if not isinstance(m.get(c), int) or m[c] < 0:
                    errores.append(f"{r['id']}: métrica «{c}» ausente o no válida.")
    return errores


# ---------------------------------------------------------------- ensamblar y cotejar

def ensamblar(pieza, d):
    """Texto final de la pieza, listo para pegar como texto de la imagen en WhatsApp."""
    p = d["proyecto"]
    est = {r["id"]: r for r in d["estudios"]}
    citas = [f"{est[s]['cita_breve']} https://doi.org/{est[s]['doi']}" for s in pieza["estudios"]]
    fuente = "📚 *Fuente:* " if len(citas) == 1 else "📚 *Fuentes:*\n"
    bloques = [pieza["secciones"]["gancho"].strip()] if pieza.get("secciones") else []
    bloques += [f"📊 *{pieza['titulo']}*", cuerpo(pieza),
               fuente + "\n".join(citas),
               f"{p['cierre']}\n🔗 {p['enlace']}"]
    return "\n\n".join(bloques) + "\n"


def enlace_whatsapp(texto):
    """Enlace que abre WhatsApp con el texto ya escrito; se elige el grupo y se envía."""
    from urllib.parse import quote
    return "https://wa.me/?text=" + quote(texto, safe="")


def formato_whatsapp(texto):
    """Errores de formato que WhatsApp no interpretaría como se espera."""
    obs = []
    for marca, nombre in (("*", "negrita"), ("_", "cursiva"), ("~", "tachado")):
        for n, linea in enumerate(texto.splitlines(), 1):
            if "http" in linea:
                continue
            if linea.count(marca) % 2:
                obs.append(f"{nombre} sin cerrar en la línea {n}.")
            for m in re.finditer(re.escape(marca) + r"([^" + re.escape(marca) + r"\n]+)" + re.escape(marca), linea):
                interior = m.group(1)
                if interior != interior.strip():
                    obs.append(f"{nombre} con espacio junto a la marca en la línea {n}: «{m.group(0)}».")
    if "**" in texto or re.search(r"^#+\s", texto, re.M) or re.search(r"\[[^\]]+\]\([^)]+\)", texto):
        obs.append("usa marcas de Markdown que WhatsApp no interpreta (**, #, [texto](enlace)).")
    return obs


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
            return obs
        if s in sup_est:
            obs.append(f"{s}: superado por {sup_est[s]}; actualizar la cita.")
            continue
        if e["estado"] != "VERIFICADO":
            obs.append(f"{s}: {e['estado']}. {e['razon']}".strip())
        if not e.get("doi"):
            obs.append(f"{s}: sin DOI.")
        if estricto and not e.get("folio"):
            obs.append(f"{s}: sin folio (página o tabla del texto completo).")
    n = palabras(cuerpo(pieza))
    minimo = PALABRAS[0] - 10 * (len(pieza["estudios"]) - 1)  # dos fuentes dejan menos espacio
    if not minimo <= n <= PALABRAS[1]:
        obs.append(f"cuerpo de {n} palabras (margen {minimo}–{PALABRAS[1]}).")
    if len(pieza["titulo"]) > TITULO_MAX:
        obs.append(f"título de {len(pieza['titulo'])} caracteres; la notificación muestra unos {TITULO_MAX}.")
    if pieza.get("secciones"):
        g = pieza["secciones"]["gancho"].strip()
        if len(g) > GANCHO_MAX:
            obs.append(f"gancho de {len(g)} caracteres; la vista previa muestra unos {GANCHO_MAX}.")
        if re.search(r"[*_~`]", g):
            obs.append("el gancho lleva marcas de formato, que la notificación muestra como símbolos.")
        if "¿" not in pieza["secciones"]["conclusion"]:
            obs.append("la conclusión no cierra con una pregunta abierta a los colegas.")
    if "*" not in cuerpo(pieza):
        obs.append("sin negritas en el hallazgo principal.")
    if "¿" not in cuerpo(pieza):
        obs.append("sin pregunta abierta a los colegas al final.")
    texto = ensamblar(pieza, d)
    if len(texto) > p["limite_caracteres"]:
        obs.append(f"{len(texto)} caracteres; como texto de la imagen, WhatsApp admite "
                   f"{p['limite_caracteres']}.")
    obs += formato_whatsapp(texto)
    for termino in p.get("excluir", []):
        if termino.lower() in texto.lower():
            obs.append(f"menciona «{termino}», que no corresponde en este canal.")
    if p["enlace"] not in texto:
        obs.append("falta el enlace del grupo.")
    return obs


def ventana(d, desde, dias):
    hasta = desde + timedelta(days=dias)
    return [r for r in vigentes(d["piezas"])
            if desde.isoformat() <= r["fecha"] <= hasta.isoformat()]


def pais_principal(e):
    """País de la afiliación del primer autor (el primero de `paises`)."""
    return e["paises"][0] if e.get("paises") else "—"


def diversidad(d, piezas):
    """Regiones de un conjunto de piezas y avisos de diversidad geográfica."""
    est = {r["id"]: r for r in d["estudios"]}
    usados = [est[s] for r in piezas for s in r["estudios"] if s in est]
    regiones = sorted({e["region"] for e in usados})
    avisos = []
    if not {"México", "Argentina", "América Latina"} & set(regiones):
        avisos.append("ningún estudio de América Latina")
    if "Asia" not in regiones:
        avisos.append("ningún estudio de Asia")
    if len(usados) >= 4:
        conteo = {}
        for e in usados:
            conteo[pais_principal(e)] = conteo.get(pais_principal(e), 0) + 1
        pais, n = max(conteo.items(), key=lambda x: x[1])
        if n > len(usados) / 2:
            avisos.append(f"{n} de {len(usados)} fuentes con primer autor en {pais}")
    return regiones, avisos


def cobertura(d):
    """Países con estudios vigentes, separados entre miembros de la OCDE y el resto."""
    sup = superados(d["estudios"])
    por_pais = {}
    for e in d["estudios"]:
        if e["id"] in sup or e["estado"] != "VERIFICADO":
            continue
        for pais in e["paises"]:
            if not pais.startswith("consorcio"):
                por_pais.setdefault(pais, []).append(e)
    ocde = d["proyecto"]["ocde"]
    return ({c: por_pais[c] for c in ocde if c in por_pais},
            {c: v for c, v in sorted(por_pais.items()) if c not in ocde},
            [c for c in ocde if c not in por_pais])


# ---------------------------------------------------------------- horarios

def tasa(m):
    """Interacción por cada 100 integrantes: (reacciones + respuestas) / miembros."""
    return 100 * (m["reacciones"] + m["respuestas"]) / m["miembros"] if m["miembros"] else 0.0


def horarios(d):
    """Resumen por franja horaria de las piezas ya medidas."""
    medidas = [r for r in d["piezas"] if r.get("metricas")]
    filas = {}
    for r in medidas:
        filas.setdefault(r["hora"], []).append(r)
    resumen = []
    for h in sorted(set(d["proyecto"]["franjas"]) | set(filas)):
        rs = filas.get(h, [])
        n = len(rs)
        if n:
            ms = [r["metricas"] for r in rs]
            resumen.append({"hora": h, "n": n,
                            "tasa": sum(tasa(m) for m in ms) / n,
                            "lectura": sum(100 * m["leidos"] / m["miembros"] for m in ms if m["miembros"]) / n,
                            "nuevos": sum(m["nuevos"] for m in ms) / n})
        else:
            resumen.append({"hora": h, "n": 0, "tasa": None, "lectura": None, "nuevos": None})
    return resumen


def recomendacion(resumen):
    medidas = [f for f in resumen if f["n"]]
    sin_dos = [f["hora"] for f in resumen if f["n"] < 2]
    if not medidas:
        return "Todavía no hay métricas registradas."
    mejor = max(medidas, key=lambda f: (f["tasa"], f["nuevos"]))
    texto = (f"Por ahora destaca {mejor['hora']} ({mejor['tasa']:.1f} interacciones por cada 100 "
             f"integrantes, {mejor['nuevos']:.1f} nuevos en promedio).")
    if sin_dos:
        texto += (f" Aún faltan al menos dos mediciones en {', '.join(sin_dos)}; con tan pocos datos, "
                  "la lectura es orientativa.")
    else:
        texto += (" Con dos mediciones por franja ya puede concentrarse la mayoría de las publicaciones "
                  "en las dos mejores franjas, y conservar una de cada cuatro para seguir probando.")
    return texto


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

def escribir_lote(d, out, desde, nombre, cab):
    p = d["proyecto"]
    lote = ventana(d, desde, 30)
    regiones, avisos = diversidad(d, lote)
    lineas = [cab, f"# Lote — {p['nombre']}\n",
              f"Piezas del {desde.isoformat()} al {(desde + timedelta(days=30)).isoformat()}, "
              f"cada {p['frecuencia_dias']} días. Cada pieza se publica como un solo mensaje: "
              f"la tarjeta (`generados/tarjetas/`) con el bloque de texto como descripción.\n",
              f"Regiones de las fuentes: {', '.join(regiones) or '—'}."
              + (f" Falta: {'; '.join(avisos)}." if avisos else "") + "\n"]
    for r in lote:
        obs = problemas_pieza(r, d)
        texto = ensamblar(r, d)
        lineas.append(f"---\n\n## {r['fecha']} · {r['hora']} · {r['id']}\n")
        lineas.append(f"{len(texto)} caracteres · {palabras(cuerpo(r))} palabras en el cuerpo.\n")
        lineas.append("> Antes de publicar: " + " ".join(obs) + "\n" if obs else "> Lista para publicar.\n")
        lineas.append(f"[Abrir en WhatsApp con el texto listo]({enlace_whatsapp(texto)})\n")
        lineas.append("```\n" + texto + "```\n")
    (out / nombre).write_text("\n".join(lineas) + "\n", encoding="utf-8")


def generar(d, proyecto, con_tarjetas=True, desde=None):
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

    for r in vig:
        (piezas_dir / f"{r['fecha']}_{r['id']}.txt").write_text(ensamblar(r, d), encoding="utf-8")

    # Enlaces para enviar por WhatsApp, en orden de publicación
    lineas = [cab, f"# Envío por WhatsApp — {p['nombre']}\n",
              "Cada enlace abre WhatsApp con el texto de la pieza ya escrito: se elige el grupo, se adjunta la "
              "tarjeta del día (`generados/tarjetas/`) si se desea y se envía. WhatsApp no permite que un sistema "
              "externo publique por sí solo en un grupo creado desde una cuenta personal.\n",
              "| Fecha | Hora | Pieza | Título | Enviar |", "|---|---|---|---|---|"]
    for r in vig:
        if r["fecha"] >= hoy.isoformat():
            lineas.append(f"| {r['fecha']} | {r['hora']} | {r['id']} | {r['titulo'].replace('|', '/')} | "
                          f"[Abrir en WhatsApp]({enlace_whatsapp(ensamblar(r, d))}) |")
    (out / "whatsapp.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    # Lote de los próximos 30 días y lotes con fecha de inicio (lote_AAAA-MM-DD.md)
    escribir_lote(d, out, hoy, "lote.md", cab)
    fechas = {f.stem[5:] for f in out.glob("lote_*.md")} | ({desde.isoformat()} if desde else set())
    for f in sorted(fechas):
        escribir_lote(d, out, date.fromisoformat(f), f"lote_{f}.md", cab)

    # Calendario
    lineas = [cab, f"# Calendario — {p['nombre']}\n",
              f"Registro actualizado el {p['actualizado_el']}. Frecuencia: cada {p['frecuencia_dias']} días. "
              f"Franjas en prueba: {', '.join(p['franjas'])}.\n",
              "| Fecha | Hora | Pieza | Estado | Tema | Estudios (región) | Interacción /100 |",
              "|---|---|---|---|---|---|---|"]
    for r in sorted(d["piezas"], key=lambda r: (r["fecha"], r["id"])):
        ident = f"~~{r['id']}~~ (superada por {sup_p[r['id']]})" if r["id"] in sup_p else r["id"]
        estudios = ", ".join(f"{s} ({est[s]['region']})" if s in est else s for s in r["estudios"])
        m = r.get("metricas")
        lineas.append(f"| {r['fecha']} | {r['hora']} | {ident} | {r['estado']} | "
                      f"{r['titulo'].replace('|', '/')} | {estudios} | {f'{tasa(m):.1f}' if m else '—'} |")
    (out / "calendario.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    # Horarios
    res = horarios(d)
    lineas = [cab, f"# Horarios — {p['nombre']}\n",
              f"Ventana de publicación: {p['ventana_horaria'][0]}–{p['ventana_horaria'][1]}. "
              "Interacción = (reacciones + respuestas) por cada 100 integrantes; lectura = leídos por cada "
              "100 integrantes, según «Info. del mensaje»; nuevos = integrantes que se unen en las 24 horas "
              "siguientes.\n",
              "| Franja | Mediciones | Interacción /100 | Lectura /100 | Nuevos |", "|---|---|---|---|---|"]
    for f in res:
        if f["n"]:
            lineas.append(f"| {f['hora']} | {f['n']} | {f['tasa']:.1f} | {f['lectura']:.0f} | {f['nuevos']:.1f} |")
        else:
            lineas.append(f"| {f['hora']} | 0 | — | — | — |")
    lineas.append("\n" + recomendacion(res))
    (out / "horarios.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    # Cobertura por país
    en_ocde, fuera, faltan = cobertura(d)
    lineas = [cab, f"# Cobertura por país — {p['nombre']}\n",
              "Países de afiliación de los autores de los estudios vigentes y verificados. Los datos de consorcios "
              "multinacionales no se desglosan por país.\n",
              f"## OCDE: {len(en_ocde)} de {len(p['ocde'])} países\n",
              "| País | Estudios | Como primer autor |", "|---|---|---|"]
    for c, es in sorted(en_ocde.items(), key=lambda x: -len(x[1])):
        primeros = sum(1 for e in es if pais_principal(e) == c)
        lineas.append(f"| {c} | {', '.join(e['id'] for e in es)} | {primeros} |")
    lineas.append(f"\n## Fuera de la OCDE ({len(fuera)})\n")
    lineas += [f"- {c}: {', '.join(e['id'] for e in es)}" for c, es in fuera.items()]
    lineas.append(f"\n## Miembros de la OCDE sin estudios ({len(faltan)})\n")
    lineas.append(", ".join(faltan) + ".")
    pend = p.get("pendientes_cobertura", [])
    if pend:
        lineas.append(f"\n## Búsquedas pendientes ({len(pend)})\n")
        lineas += [f"- **{x['pais']}** ({x['fecha']}): {x['nota']}" for x in pend]
    (out / "cobertura.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    # Pendientes
    ev = vigentes(d["estudios"])
    lineas = [cab, "# Pendientes y por verificar\n"]
    for estado in ("PENDIENTE", "POR VERIFICAR"):
        filas = [r for r in ev + vig if r["estado"] == estado]
        lineas.append(f"## {estado} ({len(filas)})\n")
        lineas += [f"- **{r['id']}** — {r.get('titulo') or r.get('referencia_corta')}. {r['razon']}"
                   for r in filas]
        lineas.append("")
    por_medir = [r for r in vig if r["fecha"] < hoy.isoformat() and not r.get("metricas")]
    lineas.append(f"## Publicadas sin métricas ({len(por_medir)})\n")
    lineas += [f"- **{r['id']}** — {r['fecha']} {r['hora']}" for r in por_medir]
    sin_folio = [r for r in ev if not r["folio"]]
    lineas.append(f"\n## Sin folio ({len(sin_folio)} de {len(ev)} estudios vigentes)\n")
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
    lineas.append(f"\n## Horario\n\n{recomendacion(res)}")
    proximas = [r for r in vig if r["fecha"] >= hoy.isoformat()][:3]
    lineas.append("\n## Próximas publicaciones\n")
    lineas += [f"- {r['fecha']} {r['hora']} — {r['id']}: {r['titulo']}" for r in proximas]
    lineas.append("\n## Estudios del registro\n")
    for e in d["estudios"]:
        marca = f" (superado por {sup_e[e['id']]})" if e["id"] in sup_e else ""
        doi = f" https://doi.org/{e['doi']}" if e["doi"] else ""
        lineas.append(f"- **{e['id']}**{marca} — {e['estado']} — {e['region']} — {e['cita']}{doi}")
    sup = [r for r in d["estudios"] + d["piezas"] if r.get("supersede")]
    if sup:
        lineas.append("\n## Registros reemplazados\n")
        lineas += [f"- {r['supersede']} → {r['id']} ({r['verificado_el'] or 'sin fecha'}): {r['razon']}"
                   for r in sup]
    (out / "handoff.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    archivos = ["lote.md", "whatsapp.md", "calendario.md", "horarios.md", "cobertura.md", "pendientes.md", "handoff.md",
                f"piezas/ ({len(vig)})"]
    if con_tarjetas:
        t_dir = out / "tarjetas"
        if t_dir.exists():
            shutil.rmtree(t_dir)
        hechas = tarjetas(d, t_dir)
        archivos.append(f"tarjetas/ ({len(hechas)})" if hechas is not None
                        else "tarjetas omitidas: instalar Pillow (pip install pillow)")
    return archivos


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accion", choices=["validar", "generar", "cotejo", "metricas", "horarios", "cerrar"])
    ap.add_argument("objetivo", nargs="?",
                    help="en cotejo: desde qué fecha (AAAA-MM-DD); en metricas: la pieza (P-xxx)")
    ap.add_argument("--proyecto", default="difusion/red-psicologos")
    ap.add_argument("--dias", type=int, default=30, help="en cotejo: días a revisar (por defecto 30)")
    ap.add_argument("--estricto", action="store_true", help="en cotejo: exige folio en cada estudio citado")
    ap.add_argument("--sin-tarjetas", action="store_true", help="no regenera las imágenes")
    ap.add_argument("--desde", help="en generar o cerrar: escribe además generados/lote_AAAA-MM-DD.md desde esa fecha")
    for c in CAMPOS_METRICAS:
        ap.add_argument(f"--{c}", type=int)
    ap.add_argument("--publicada", help="en metricas: fecha y hora reales, «AAAA-MM-DD HH:MM»")
    a = ap.parse_args()
    d = cargar(a.proyecto)

    errores = validar(d)
    if errores:
        print("El registro tiene errores:")
        for e in errores:
            print(f"  - {e}")
        return 1

    if a.accion == "metricas":
        piezas = {r["id"]: r for r in d["piezas"]}
        if a.objetivo not in piezas:
            ap.error("metricas requiere el identificador de una pieza existente (P-xxx)")
        faltan = [c for c in CAMPOS_METRICAS if getattr(a, c) is None]
        if faltan:
            ap.error("faltan: " + ", ".join(f"--{c}" for c in faltan))
        r = piezas[a.objetivo]
        r["metricas"] = {c: getattr(a, c) for c in CAMPOS_METRICAS}
        r["metricas"]["publicada"] = a.publicada or f"{r['fecha']} {r['hora']}"
        r["metricas"]["registrada_el"] = date.today().isoformat()
        guardar(d, a.proyecto)
        print(f"{a.objetivo}: {tasa(r['metricas']):.1f} interacciones por cada 100 integrantes; "
              f"{r['metricas']['nuevos']} nuevos.")
        return 0

    if a.accion == "horarios":
        for f in horarios(d):
            print(f"  {f['hora']}: " + (f"{f['n']} mediciones, {f['tasa']:.1f} interacción/100, "
                                        f"{f['nuevos']:.1f} nuevos" if f["n"] else "sin mediciones"))
        print(recomendacion(horarios(d)))
        return 0

    if a.accion == "cotejo":
        desde = date.fromisoformat(a.objetivo) if a.objetivo else date.today()
        piezas = ventana(d, desde, a.dias)
        print(f"Cotejo del {desde.isoformat()} al {(desde + timedelta(days=a.dias)).isoformat()}: "
              f"{len(piezas)} piezas.")
        total = 0
        for r in piezas:
            obs = problemas_pieza(r, d, a.estricto)
            if obs:
                total += len(obs)
                print(f"  {r['fecha']} {r['hora']} {r['id']}:")
                for o in obs:
                    print(f"    - {o}")
        regiones, avisos = diversidad(d, piezas)
        print(f"Regiones: {', '.join(regiones) or '—'}." + (f" Aviso: {'; '.join(avisos)}." if avisos else ""))
        if not total:
            print("Sin observaciones: todo lo citado está VERIFICADO y vigente, y el formato es válido.")
            return 0
        print(f"{total} observaciones. Esas piezas no salen hasta resolverlas o retirar la cita.")
        return 1

    if a.accion == "validar":
        print(f"Registro válido: {len(d['estudios'])} estudios, {len(d['piezas'])} piezas.")
        return 0

    desde = date.fromisoformat(a.desde) if a.desde else None
    archivos = generar(d, a.proyecto, con_tarjetas=not a.sin_tarjetas, desde=desde)
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
        _, avisos = diversidad(d, ventana(d, date.today(), 30))
        if avisos:
            print(f"Aviso de diversidad en los próximos 30 días: {'; '.join(avisos)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
