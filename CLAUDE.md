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

## Rutina de cierre (al terminar cada sesión o cada jueves)

1. Agregar los registros nuevos y marcar los superados en `registro.json`.
2. Actualizar `caso.actualizado_el`.
3. `python3 herramientas/registro.py cerrar` (valida y regenera).
4. Commit de registro, fuentes y generados.

## Antes de presentar un escrito

`python3 herramientas/registro.py cotejo casos/<caso>/escritos/<escrito>.md`
(con `--despacho` para exigir folio). Si devuelve observaciones, el escrito no sale hasta resolverlas o retirar la cita.
