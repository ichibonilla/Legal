#!/usr/bin/env python3
"""Registra el resultado de un envío en enviados.log.

Uso:  python3 registrar_envio.py P-023 VERIFICADO "doble check visto a las 08:02"
      python3 registrar_envio.py P-023 NO_ENVIADO "WhatsApp Web pedía el código QR"
"""
import sys
from datetime import datetime
from pathlib import Path

if len(sys.argv) < 4 or sys.argv[2] not in ("VERIFICADO", "NO_ENVIADO"):
    sys.exit(__doc__)
linea = "\t".join([datetime.now().strftime("%Y-%m-%d %H:%M"), sys.argv[1], sys.argv[2], sys.argv[3]])
with open(Path(__file__).resolve().parent / "enviados.log", "a", encoding="utf-8") as f:
    f.write(linea + "\n")
print(linea)
