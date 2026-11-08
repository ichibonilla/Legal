#!/usr/bin/env python3
"""Pieza que toca publicar ahora en el grupo de WhatsApp de la Red.

Uso, desde esta carpeta:  python3 pieza_del_momento.py
- Código 0: imprime el id, el título y la ruta de la tarjeta, y deja el texto
  de la pieza en el portapapeles (pbcopy) para pegarlo con Cmd+V.
- Código 2: no hay pieza para esta hora.
- Código 3: la pieza de hoy ya se envió.
Toma la pieza de hoy cuya hora ya llegó (o llega en los próximos 15 minutos)
y que no figura como VERIFICADO en enviados.log.
"""
import json, subprocess, sys
from datetime import datetime, timedelta
from pathlib import Path

aqui = Path(__file__).resolve().parent
datos = json.loads((aqui / "envios.json").read_text(encoding="utf-8"))
log = aqui / "enviados.log"
enviados = set()
if log.exists():
    for linea in log.read_text(encoding="utf-8").splitlines():
        partes = linea.split("\t")
        if len(partes) >= 3 and partes[2] == "VERIFICADO":
            enviados.add(partes[1])

ahora = datetime.now()
hoy = ahora.strftime("%Y-%m-%d")
limite = (ahora + timedelta(minutes=15)).strftime("%H:%M")
de_hoy = [p for p in datos["piezas"] if p["fecha"] == hoy]
if not de_hoy:
    print("No hay pieza programada para hoy.")
    sys.exit(2)
pendientes = [p for p in de_hoy if p["id"] not in enviados and p["hora"] <= limite]
if not pendientes:
    if all(p["id"] in enviados for p in de_hoy):
        print("La pieza de hoy ya se envió.")
        sys.exit(3)
    print("La pieza de hoy aún no llega a su hora.")
    sys.exit(2)
p = pendientes[0]
subprocess.run(["pbcopy"], input=p["texto"].encode("utf-8"), check=True)
print(f"PIEZA\t{p['id']}\t{p['hora']}\t{p['titulo']}")
print(f"TARJETA\t{aqui / p['tarjeta']}")
print("TEXTO en el portapapeles (pegar con Cmd+V en la descripción de la imagen).")
