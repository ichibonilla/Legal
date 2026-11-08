# Publicación automática en el grupo «Red Psicólogos en Costa Rica»

Este paquete permite que Claude, en la Mac, publique cada pieza a su hora desde el Chrome donde WhatsApp Web ya tiene sesión, con el mismo método del mensaje diario a Alejandra.

## Contenido

- `envios.json`: las piezas programadas (fecha, hora, título, texto y tarjeta). Se genera desde el registro de la Red; no se edita a mano.
- `tarjetas/`: la imagen de cada pieza.
- `pieza_del_momento.py`: dice qué pieza toca y deja su texto en el portapapeles.
- `registrar_envio.py`: anota el resultado en `enviados.log`.

## Instalación (una sola vez)

1. Descomprimir el paquete en iCloud Drive › Poïesis › Red Psicólogos › Envíos.
2. En la app de Claude en la Mac, abrir una conversación nueva con acceso a esa carpeta y pegar la instrucción de abajo.
3. Mantener la Mac encendida, con Chrome abierto y WhatsApp Web con la sesión iniciada, a las horas de publicación.

## Instrucción para pegar en Claude, en la Mac

> Cree dos tareas programadas en esta Mac, con el nombre «Red Psicólogos · publicación en WhatsApp», en hora de Costa Rica: una a las 8:00, 11:00, 14:00 y 18:00, y otra a las 21:30, todos los días. Cada corrida hace exactamente esto:
>
> 1. Comprobación previa: confirme que la corrida tiene acceso a esta Mac. Si corre en la nube, termine con «Corrida en la nube, sin acceso a la Mac: no se envió».
> 2. En la carpeta «Red Psicólogos/Envíos», ejecute `python3 pieza_del_momento.py`. Si devuelve código 2 o 3, termine sin hacer nada más.
> 3. Abra web.whatsapp.com en Chrome y espere al menos 30 segundos. Busque y abra solo el grupo «Red Psicólogos en Costa Rica». Ningún otro chat; no lea ni abra otras conversaciones. Si tras 90 segundos sigue el código QR, registre NO_ENVIADO con esa causa y termine.
> 4. Adjunte la imagen indicada en TARJETA (clip › Fotos y videos). En el campo de descripción, pegue el texto con Cmd+V (ya está en el portapapeles) y envíe una sola vez.
> 5. Verifique que el mensaje quede bajo «Hoy» con doble check. Si aparece «no enviado», recargue y use «Reintentar». No lo dé por enviado sin ver el doble check.
> 6. Registre: `python3 registrar_envio.py <ID> VERIFICADO "<hora y verificación>"`, o NO_ENVIADO con la causa.
> 7. Informe en una frase: salió o no salió, a qué hora y qué pieza. Envíe además una notificación al teléfono con ese resultado.

## Actualización mensual

Cada mes, la rutina de la Red regenera `envios.json` y las tarjetas con el lote nuevo. Basta reemplazar esos dos elementos en la carpeta de la Mac; `enviados.log` se conserva.
