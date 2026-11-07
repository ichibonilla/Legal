# Repositorio Legal — reglas de trabajo

Material confidencial. No se publica fuera del repositorio.

## Una sola fuente por caso

- `casos/<caso>/registro.json` es la fuente única. Todo lo que está en `casos/<caso>/generados/` (cronología, handoff, pendientes) se regenera desde ahí y no se edita a mano.
- `casos/<caso>/fuentes/` guarda los documentos primarios tal como llegaron; `documentos/` los análisis; `escritos/` los borradores para presentar.

## Registros

- Estados: VERIFICADO (cotejado contra la fuente, con fecha en `verificado_el`), POR VERIFICAR, PENDIENTE.
- No se borra. Un dato corregido se registra de nuevo con `supersede` (ID reemplazado) y `razon`.
- `folio` queda vacío hasta tener expediente certificado; ese día se completa de una sentada.
- En los escritos, cada afirmación de hecho o de norma se cita como `[R-xxx]` o `[N-xxx]`.
- Para cotejar un mensaje de chat citado en `fuente`: `python3 herramientas/chats.py ver casos/<caso>/fuentes/<chat>.zip "<fecha y hora>"`; para buscar en un chat: `chats.py buscar`.

## Identidad visual

- Toda carta y todo documento de Poïesis usa solo la paleta institucional: `#131237`, `#2F2E47`, `#5C6684`, `#D1D0CB` y blanco. Títulos en Safira March; texto en una tipografía sobria.
- La versión Word de un escrito se genera con esa paleta: `python3 herramientas/escrito_docx.py casos/<caso>/escritos/<escrito>.md --caso casos/<caso>` (`--pdf` para la versión PDF). El encabezado dice solo «Grupo Poïesis»; `--confidencial` lo marca como confidencial cuando el documento es interno.

## Rutina de cierre (al terminar cada sesión o cada jueves)

1. Agregar los registros nuevos y marcar los superados en `registro.json`.
2. Actualizar `caso.actualizado_el`.
3. `python3 herramientas/registro.py cerrar` (valida y regenera).
4. Commit de registro, fuentes y generados.

## Antes de presentar un escrito

`python3 herramientas/registro.py cotejo casos/<caso>/escritos/<escrito>.md`
(con `--despacho` para exigir folio). Si devuelve observaciones, el escrito no sale hasta resolverlas o retirar la cita.

## Difusión: Red Psicólogos en Costa Rica

Mismo método, aplicado al calendario del grupo de WhatsApp. No es material de caso: son piezas para publicar en el grupo.

- `difusion/red-psicologos/registro.json` es la fuente única: `estudios` (S-xxx, fuente científica y hallazgos cotejados) y `piezas` (P-xxx, mensaje, fecha y estudios que cita). Mismos estados y mismos campos `verificado_el`, `supersede` y `razon`; no se borra.
- `folio` en un estudio es la página o tabla del texto completo donde consta la cifra; queda vacío mientras el cotejo se haya hecho solo contra el resumen.
- Una pieza cada tres días, preparada con 30 días de antelación; unas 90 palabras, emojis discretos, cita APA con DOI y el enlace del grupo al final. Firma solo la Red; no se menciona a ninguna institución.
- Toda cifra de una pieza debe constar en los `hallazgos` del estudio que cita.
- `generados/` (lote para copiar, piezas en `.txt`, tarjetas en la paleta sin logotipo, calendario, pendientes, handoff) se regenera: `python3 herramientas/difusion.py cerrar`.
- Antes de publicar: `python3 herramientas/difusion.py cotejo` (próximos 30 días; `--estricto` exige folio). Si devuelve observaciones, la pieza no sale hasta resolverlas o retirar la cita.
- La rutina de cierre de cada jueves incluye este registro.
