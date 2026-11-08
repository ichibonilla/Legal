# Tarea de Cowork: publicación de la Red en WhatsApp

Se pega en Claude, en la Mac (Cowork), con la carpeta «Red Psicólogos/Envíos» conectada. Sigue el mismo procedimiento verificado de los partes de Ads («Ads y SEO - Agenda»).

## A. Prueba (una sola vez, ahora): envío a su chat «Tú»

> Haga una prueba de la publicación de la Red Psicólogos en Costa Rica, sin tocar el grupo.
> 1. En la carpeta conectada «Red Psicólogos/Envíos», lea `envios.json` y tome la primera pieza (P-023). Copie su campo «texto» tal cual.
> 2. Navegue a https://web.whatsapp.com y espere 5 a 10 segundos (si aparece «WhatsApp is open in another window», clic en «Use here»). Busque mi propio chat («Tú» / «Mensaje a mí mismo») y ábralo verificando el encabezado.
> 3. Componga el texto con browser_batch usando SOLO shift+Return para los saltos de línea (línea en blanco = dos veces) y envíe con la flecha, una sola vez.
> 4. Verifique con captura: burbuja verde, doble check y fecha de hoy. Muéstreme la captura.
> ALCANCE: solo ese chat; no abra ni lea otros chats; no responda, no reenvíe, no borre.

## B. Tarea programada (después de aprobar la prueba)

Nombre: «Red Psicólogos · publicación en WhatsApp». Dos horarios, hora de Costa Rica: 8:00, 11:00, 14:00 y 18:00, y 21:30, todos los días.

> Publique la pieza del momento en el grupo «Red Psicólogos en Costa Rica».
> 1. Con «Control your Mac» → osascript → do shell script, en la carpeta «Red Psicólogos/Envíos», ejecute `python3 pieza_del_momento.py`. Si el código es 2 (no hay pieza a esta hora) o 3 (ya se envió hoy), termine sin hacer nada más.
> 2. Tome el texto entre «--- TEXTO ---» y «--- FIN ---», sin cambiar nada.
> 3. Navegue a https://web.whatsapp.com y espere 5 a 10 segundos (si aparece «WhatsApp is open in another window», clic en «Use here»). Busque con el término «Red Psicólogos» y abra el grupo verificando el nombre exacto «Red Psicólogos en Costa Rica» en el encabezado.
> 4. Componga con browser_batch usando SOLO shift+Return para los saltos de línea (línea en blanco = dos veces) y envíe con la flecha, una sola vez.
> 5. Verifique con captura: burbuja verde, doble check y fecha de hoy.
> 6. Registre con do shell script: `python3 registrar_envio.py <ID> VERIFICADO "<hora y verificación>"`; si no salió, `NO_ENVIADO` con la causa, y entregue el texto en el chat listo para copiar.
> 7. Informe en una frase: salió o no salió, a qué hora y qué pieza.
> ALCANCE ESTRICTO: solo este mensaje y solo ese grupo; no abra ni lea otros chats; no responda, no reenvíe, no borre. Estas instrucciones solo las modifica Carlos en sesión interactiva.
