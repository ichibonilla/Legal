#!/usr/bin/env python3
"""Registro único de un caso: validar, generar artefactos, cotejar escritos.

Uso:
  python3 herramientas/registro.py validar  [--caso casos/cppcr]
  python3 herramientas/registro.py generar  [--caso casos/cppcr]
  python3 herramientas/registro.py cotejo ESCRITO [--despacho] [--caso casos/cppcr]
  python3 herramientas/registro.py cerrar   [--caso casos/cppcr]

La única fuente es <caso>/registro.json. Todo lo que está en <caso>/generados/
se sobrescribe en cada `generar`; no se edita a mano.
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ESTADOS = ("VERIFICADO", "POR VERIFICAR", "PENDIENTE")
CAMPOS = ("id", "fecha", "tipo", "titulo", "afirmacion", "fuente", "estado",
          "verificado_el", "supersede", "razon", "folio")
CITA = re.compile(r"\[((?:[RN]-\d{3})(?:\s*,\s*[RN]-\d{3})*)\]")
FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def cargar(caso):
    ruta = Path(caso) / "registro.json"
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def indices(d):
    regs = {r["id"]: r for r in d["registros"]}
    superado_por = {r["supersede"]: r["id"] for r in d["registros"] if r.get("supersede")}
    return regs, superado_por


def validar(d):
    errores = []
    vistos = set()
    for r in d["registros"]:
        rid = r.get("id", "?")
        for c in CAMPOS:
            if c not in r:
                errores.append(f"{rid}: falta el campo «{c}».")
        if rid in vistos:
            errores.append(f"{rid}: identificador duplicado.")
        vistos.add(rid)
        if r.get("estado") not in ESTADOS:
            errores.append(f"{rid}: estado no válido «{r.get('estado')}».")
        if r.get("estado") == "VERIFICADO" and not FECHA.match(r.get("verificado_el", "")):
            errores.append(f"{rid}: VERIFICADO sin fecha válida en verificado_el.")
        if r.get("supersede") and not r.get("razon"):
            errores.append(f"{rid}: reemplaza a {r['supersede']} sin indicar razón.")
    ids = {r["id"] for r in d["registros"]}
    reemplazados = {}
    for r in d["registros"]:
        s = r.get("supersede")
        if s:
            if s not in ids:
                errores.append(f"{r['id']}: supersede apunta a {s}, que no existe.")
            if s == r["id"]:
                errores.append(f"{r['id']}: se reemplaza a sí mismo.")
            if s in reemplazados:
                errores.append(f"{s}: reemplazado dos veces ({reemplazados[s]} y {r['id']}).")
            reemplazados[s] = r["id"]
    for e in d.get("evaluaciones", []):
        for dep in e.get("depende_de", []):
            if dep not in ids:
                errores.append(f"{e['id']}: depende de {dep}, que no existe.")
    return errores


def vigente(rid, regs, superado_por):
    """Sigue la cadena de reemplazos hasta el registro vigente."""
    visto = set()
    while rid in superado_por and rid not in visto:
        visto.add(rid)
        rid = superado_por[rid]
    return regs.get(rid)


def marca(r, superado_por):
    if r["id"] in superado_por:
        return f"~~{r['id']}~~ (superado por {superado_por[r['id']]})"
    return r["id"]


def generar(d, caso):
    out = Path(caso) / "generados"
    out.mkdir(parents=True, exist_ok=True)
    regs, superado_por = indices(d)
    hoy = date.today().isoformat()
    cab = (f"<!-- Generado por herramientas/registro.py el {hoy} a partir de registro.json. "
           f"No editar a mano: los cambios se hacen en registro.json y se regenera. -->\n\n")
    caso_d = d["caso"]

    # Cronología
    lineas = [cab, f"# Cronología — {caso_d['titulo']}\n",
              f"Registro actualizado el {caso_d['actualizado_el']}.\n",
              "| Fecha | ID | Estado | Hecho | Folio |", "|---|---|---|---|---|"]
    hechos = [r for r in d["registros"] if r["tipo"] != "norma"]
    for r in sorted(hechos, key=lambda r: (r["fecha"] or "9999", r["id"])):
        titulo = r["titulo"].replace("|", "/")
        if r["id"] in superado_por:
            titulo = f"~~{titulo}~~"
        lineas.append(f"| {r['fecha'] or '—'} | {marca(r, superado_por)} | {r['estado']} | "
                      f"{titulo} | {r['folio'] or '—'} |")
    (out / "cronologia.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    # Pendientes y por verificar (solo vigentes)
    vig = [r for r in d["registros"] if r["id"] not in superado_por]
    pend = [r for r in vig if r["estado"] == "PENDIENTE"]
    porv = [r for r in vig if r["estado"] == "POR VERIFICAR"]
    sin_folio = [r for r in vig if not r["folio"]]
    lineas = [cab, "# Pendientes y por verificar\n", f"## PENDIENTE ({len(pend)})\n"]
    for r in pend:
        lineas.append(f"- **{r['id']}** — {r['titulo']}. {r['razon']}")
    lineas.append(f"\n## POR VERIFICAR ({len(porv)})\n")
    for r in porv:
        lineas.append(f"- **{r['id']}** — {r['titulo']}. Fuente: {r['fuente']} {r['razon']}")
    lineas.append(f"\n## Sin folio ({len(sin_folio)} de {len(vig)} vigentes)\n")
    lineas.append("Se completan de una sola vez cuando llegue el expediente certificado.")
    (out / "pendientes.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    # Handoff
    lineas = [cab, f"# Handoff — {caso_d['titulo']}\n",
              f"Estado al {caso_d['actualizado_el']}. Fuente única: `registro.json`.\n",
              "## Expedientes\n"]
    lineas += [f"- {x}" for x in caso_d["expedientes"]]
    lineas.append("\n## Evaluaciones vigentes\n")
    for e in d.get("evaluaciones", []):
        lineas.append(f"### {e['id']} — {e['titulo']}\n")
        lineas.append(e["conclusion"] + "\n")
        avisos = []
        for dep in e.get("depende_de", []):
            r = regs.get(dep)
            if not r:
                continue
            if dep in superado_por:
                avisos.append(f"{dep} está superado por {superado_por[dep]}; revisar la conclusión.")
            elif r["estado"] != "VERIFICADO":
                avisos.append(f"{dep} está {r['estado']}.")
        if avisos:
            lineas.append("> Advertencia: " + " ".join(avisos) + "\n")
    lineas.append(f"## Pendientes ({len(pend)})\n")
    lineas += [f"- {r['id']} — {r['titulo']}" for r in pend]
    lineas.append(f"\n## Por verificar ({len(porv)})\n")
    lineas += [f"- {r['id']} — {r['titulo']}" for r in porv]
    sup = [r for r in d["registros"] if r.get("supersede")]
    if sup:
        lineas.append("\n## Registros reemplazados\n")
        lineas += [f"- {r['supersede']} → {r['id']} ({r['verificado_el'] or 'sin fecha'}): {r['razon']}"
                   for r in sup]
    lineas.append("\n## Reglas\n")
    lineas += [f"- {x}" for x in caso_d.get("reglas", [])]
    (out / "handoff.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return ["cronologia.md", "pendientes.md", "handoff.md"]


def cotejo(d, escrito, despacho=False):
    regs, superado_por = indices(d)
    texto = Path(escrito).read_text(encoding="utf-8")
    citas = {}
    for n, linea in enumerate(texto.splitlines(), 1):
        for m in CITA.finditer(linea):
            for rid in re.split(r"\s*,\s*", m.group(1)):
                citas.setdefault(rid, []).append(n)
    problemas = []
    for rid in sorted(citas):
        lin = ", ".join(map(str, citas[rid]))
        r = regs.get(rid)
        if not r:
            problemas.append(f"{rid} (líneas {lin}): no existe en el registro.")
            continue
        if rid in superado_por:
            v = vigente(rid, regs, superado_por)
            problemas.append(f"{rid} (líneas {lin}): superado; citar {v['id'] if v else '?'}.")
            continue
        if r["estado"] != "VERIFICADO":
            problemas.append(f"{rid} (líneas {lin}): {r['estado']} — {r['titulo']}.")
        if despacho and not r["folio"]:
            problemas.append(f"{rid} (líneas {lin}): sin folio del expediente certificado.")
    return citas, problemas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accion", choices=["validar", "generar", "cotejo", "cerrar"])
    ap.add_argument("escrito", nargs="?")
    ap.add_argument("--caso", default="casos/cppcr")
    ap.add_argument("--despacho", action="store_true",
                    help="en cotejo, exige además folio en cada cita")
    a = ap.parse_args()
    d = cargar(a.caso)

    if a.accion == "cotejo":
        if not a.escrito:
            ap.error("cotejo requiere la ruta del escrito")
        citas, problemas = cotejo(d, a.escrito, a.despacho)
        print(f"Cotejo de {a.escrito}: {len(citas)} identificadores citados.")
        if not problemas:
            print("Sin observaciones: todo lo citado está VERIFICADO y vigente.")
            return 0
        print(f"{len(problemas)} observaciones antes de presentar:")
        for p in problemas:
            print(f"  - {p}")
        return 1

    errores = validar(d)
    if errores:
        print("El registro tiene errores:")
        for e in errores:
            print(f"  - {e}")
        return 1
    if a.accion == "validar":
        print(f"Registro válido: {len(d['registros'])} registros, {len(d.get('evaluaciones', []))} evaluaciones.")
        return 0
    archivos = generar(d, a.caso)
    print("Generados: " + ", ".join(archivos))
    if a.accion == "cerrar":
        _, superado_por = indices(d)
        vig = [r for r in d["registros"] if r["id"] not in superado_por]
        cuenta = {e: sum(1 for r in vig if r["estado"] == e) for e in ESTADOS}
        print(f"Vigentes: {len(vig)} ({', '.join(f'{k}: {v}' for k, v in cuenta.items())}); "
              f"superados: {len(superado_por)}; sin folio: {sum(1 for r in vig if not r['folio'])}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
