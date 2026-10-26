#!/usr/bin/env python3
"""Lectura de exportaciones de WhatsApp guardadas en fuentes/, para cotejar citas.

Uso:
  python3 herramientas/chats.py ver    FUENTE.zip "20/4/26 1:31:25 p. m."
  python3 herramientas/chats.py buscar FUENTE.zip PATRON [--desde AAAA-MM-DD] [--hasta AAAA-MM-DD] [--quien TEXTO]

Lee el _chat.txt directamente del .zip, sin extraerlo. Admite la exportación en
inglés ([M/D/YY, H:MM:SS AM]) y en español ([D/M/YY, H:MM:SS a. m.]). En «ver», la
marca es la fecha y hora tal como aparece en la exportación y en el campo
`fuente` del registro; basta con el comienzo («20/4/26 1:31»).
"""
import argparse
import re
import signal
import sys
import zipfile
from datetime import datetime

CABECERA = re.compile(r"^\W*\[(\d{1,2})/(\d{1,2})/(\d{2}), (\d{1,2}):(\d{2}):(\d{2})\W+([AaPp])\.?\W*[Mm]\.?\] ([^:]+): ?(.*)$")


def normalizar(marca):
    """«[20/4/26, 1:31:25 p. m.]» y «20/4/26 1:31:25 p. m.» quedan como «20/4/26 1:31:25 pm»."""
    m = re.sub(r"[\[\],]", " ", marca).replace(".", "").lower()
    return re.sub(r"\b([ap]) m$", r"\1m", " ".join(m.split()))


def mensajes(fuente):
    with zipfile.ZipFile(fuente) as z:
        texto = z.read("_chat.txt").decode("utf-8", errors="replace")
    espanol = bool(re.search(r"\d\W[ap]\.\W*m\.\]", texto[:5000]))
    actual = None
    for linea in texto.splitlines():
        m = CABECERA.match(linea)
        if m:
            if actual:
                yield actual
            a, b, aa, h, mi, s, ap, quien, cuerpo = m.groups()
            dia, mes = (a, b) if espanol else (b, a)
            hora = int(h) % 12 + (12 if ap.lower() == "p" else 0)
            fecha = datetime(2000 + int(aa), int(mes), int(dia), hora, int(mi), int(s))
            marca = normalizar(linea[:linea.index("]") + 1])
            actual = {"fecha": fecha, "marca": marca, "quien": quien.strip(), "texto": cuerpo}
        elif actual:
            actual["texto"] += "\n" + linea
    if actual:
        yield actual


def main():
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # permite cortar la salida con head
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accion", choices=["ver", "buscar"])
    ap.add_argument("fuente")
    ap.add_argument("patron", help="marca de fecha y hora (ver) o expresión regular (buscar)")
    ap.add_argument("--desde")
    ap.add_argument("--hasta")
    ap.add_argument("--quien")
    a = ap.parse_args()

    if a.accion == "ver":
        buscada = normalizar(a.patron)
        hallados = [m for m in mensajes(a.fuente) if m["marca"].startswith(buscada)]
        for m in hallados:
            print(f"[{m['marca']}] {m['quien']}:\n{m['texto']}\n")
        if not hallados:
            print(f"No hay mensajes con la marca «{a.patron}» en {a.fuente}.")
            return 1
        return 0

    rx = re.compile(a.patron, re.I)
    desde = datetime.fromisoformat(a.desde) if a.desde else None
    hasta = datetime.fromisoformat(a.hasta) if a.hasta else None
    n = 0
    for m in mensajes(a.fuente):
        if desde and m["fecha"] < desde or hasta and m["fecha"] > hasta:
            continue
        if a.quien and a.quien.lower() not in m["quien"].lower():
            continue
        if rx.search(m["texto"]):
            n += 1
            resumen = " / ".join(m["texto"].splitlines())[:220]
            print(f"[{m['marca']}] {m['quien']}: {resumen}")
    print(f"{n} mensajes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
