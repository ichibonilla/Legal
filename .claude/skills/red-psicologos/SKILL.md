---
name: red-psicologos
description: Prepara, coteja y mide las piezas de evidencia científica para el grupo de WhatsApp «Red Psicólogos en Costa Rica»: metaanálisis y estudios de alto grado de psicología, psicoanálisis y psicodinámica, en unas 90 palabras, con cita APA, DOI, tarjeta visual y el enlace del grupo. Usar cuando se pida preparar el lote del mes, escribir o corregir una pieza, buscar estudios para el grupo, registrar métricas (reacciones, respuestas, leídos, nuevos integrantes), elegir la hora de publicación o revisar cómo se ve un texto en WhatsApp.
---

# Red Psicólogos en Costa Rica

Una pieza cada tres días, preparada con 30 días de antelación, para un grupo de WhatsApp de profesionales en psicología. El propósito es doble: que cada pieza sea útil en la práctica clínica y que el grupo crezca porque los colegas la reenvían.

La fuente única es `difusion/red-psicologos/registro.json`. Todo lo demás se genera con `herramientas/difusion.py` y no se edita a mano.

## 1. Fuentes

- Solo evidencia de alto grado que se siga sosteniendo: metaanálisis, metaanálisis en red, revisiones sistemáticas (Cochrane incluidas), grandes bases de datos y consorcios internacionales, y revisiones de alto impacto.
- Origen internacional, en las regiones admitidas por el registro: Estados Unidos, México, Argentina, Europa y Asia. Cada lote incluye al menos una fuente de América Latina y una de Asia cuando exista evidencia de ese nivel; si no existe, se deja constancia en el registro como PENDIENTE, sin rebajar el estándar.
- Campos clínicos: psicoterapia en general, psicoanálisis y psicodinámica como eje, y de vez en cuando hallazgos que matizan o cuestionan el enfoque psicodinámico. Eso le da credibilidad al grupo frente a colegas de otras orientaciones.
- Antes de usar un estudio, revisar si fue superado por una actualización o si recibió críticas publicadas. Si las recibió, la pieza las menciona.

## 2. Cotejo de cada estudio

1. Confirmar la cita (autores, año, título, revista, volumen, páginas) y el DOI en al menos una fuente primaria: PubMed, el sitio de la revista o el repositorio institucional.
2. Copiar a `hallazgos` cada cifra y cada afirmación que se piense usar, tal como constan en el resumen o el texto completo.
3. Estado:
   - VERIFICADO, con `verificado_el`, cuando todo consta en una fuente primaria.
   - POR VERIFICAR cuando una cifra solo aparece en una fuente secundaria (`razon` dice cuál falta y la fecha límite).
   - PENDIENTE cuando falta la cita o el DOI.
4. `folio` (página o tabla del texto completo) queda vacío mientras el cotejo sea solo contra el resumen.
5. Nada se borra. Una corrección es un registro nuevo con `supersede` y `razon`.

Regla de oro: **ninguna cifra entra en una pieza si no está en los `hallazgos` del estudio que cita.** Si no se puede verificar, se cambia la frase o se retira la cifra; nunca se redondea ni se infiere.

## 3. Redacción

Voz: clara, con la simpleza de Steve Jobs; cálida, amigable y objetiva; competente y segura, con modestia estratégica. Sin imperativos dirigidos a los colegas, sin condescendencia ni paternalismo, sin dramatizar ni prometer resultados. Español de Costa Rica, con tildes completas y coma decimal (r = 0,28).

Estructura de cada pieza (el registro guarda título, cuerpo y estudios; la herramienta agrega la fuente y el cierre):

```
📊 *Título: pregunta o dato, 60 caracteres como máximo*

Quién y qué: autores, año y diseño en una frase, con el tamaño de la muestra.

El hallazgo principal, *en negrita*, con su cifra. Un matiz o límite si lo hay.

💡 _Para la práctica:_ una lectura clínica breve, sin indicaciones.

¿Pregunta abierta a los colegas?
```

- Cuerpo de unas 80 a 90 palabras (de 65 a 100; menos cuando se citan dos fuentes).
- Negrita solo en lo más importante: el hallazgo y, si acaso, la idea clínica. Dos o tres fragmentos por pieza como máximo.
- Emojis como anclas visuales, no como decoración: 📊 título, 💡 práctica, 📚 fuente, 🤝 cierre, 🔗 enlace.
- Revisar cada texto de inicio a fin: hilo conductor, coherencia entre título, hallazgo, práctica y pregunta, y que no se repitan palabras en frases cercanas.

## 4. Engagement

- **La notificación es el gancho.** El título es lo único que se lee antes de abrir el mensaje: una pregunta que el colega quiera responder o una cifra que sorprenda.
- **Un solo mensaje por pieza.** La tarjeta con el texto como descripción. Así, cuando alguien reenvía la pieza, viajan juntos la cifra, la cita y el enlace para unirse. Límite: 1024 caracteres.
- **Una pregunta abierta al final** invita a responder, y las respuestas convierten el grupo en conversación entre colegas. Conviene que sea concreta y ligada a la experiencia clínica («¿Cómo la detectan en su consulta?»), no retórica.
- **Utilidad antes que volumen.** Cada pieza deja una idea aplicable. Mejor una pieza excelente que dos correctas.
- **Variedad de formatos a lo largo del mes:** dato sorprendente, mito frente a evidencia, debate entre dos estudios y hallazgo metodológico.
- **Ritmo:** cada tres días, sin publicar dos veces el mismo día y sin mensajes de seguimiento que saturen.

## 5. Formato de WhatsApp

Revisar estas reglas en el Centro de ayuda de WhatsApp (sección «Cómo dar formato a tus mensajes») al preparar cada lote, porque cambian con las versiones.

| Formato | Escritura | Nota |
|---|---|---|
| Negrita | `*texto*` | Sin espacio entre la marca y el texto. |
| Cursiva | `_texto_` | Igual. |
| Tachado | `~texto~` | Igual. |
| Monoespaciado | ` ```texto``` ` | |
| Código en línea | `` `texto` `` | |
| Lista con viñetas | `- texto` o `* texto` al inicio de la línea | |
| Lista numerada | `1. texto` al inicio de la línea | |
| Cita | `> texto` al inicio de la línea | |

- No funcionan: `**doble asterisco**`, títulos con `#` ni enlaces del tipo `[texto](url)`. El enlace se pega completo.
- La descripción de una imagen admite hasta 1024 caracteres (documentación de Meta para la plataforma de WhatsApp Business). La herramienta lo controla.
- `cotejo` detecta marcas sin cerrar, espacios junto a las marcas y sintaxis de Markdown que WhatsApp no interpreta.

## 6. Hora de publicación

- Ventana: de 8:00 a 23:00.
- Fase de prueba: cinco franjas (8:00, 11:00, 14:00, 18:00 y 21:30). Cada franja se usa dos veces en días distintos de la semana; la frecuencia de tres días ya hace rotar los días.
- Después de cada publicación, al cabo de 24 horas, se registra:
  - integrantes del grupo en ese momento;
  - leídos, según «Info. del mensaje» (mantener presionado el mensaje propio);
  - reacciones y respuestas;
  - nuevos integrantes que se unieron en esas 24 horas.

  ```
  python3 herramientas/difusion.py metricas P-xxx --miembros 210 --leidos 150 --reacciones 12 --respuestas 3 --nuevos 4
  ```
- `horarios` resume la interacción por cada 100 integrantes y los nuevos integrantes por franja. Con dos mediciones por franja, la mayoría de las publicaciones se concentra en las dos mejores, y una de cada cuatro se reserva para seguir probando. Con pocos datos, la lectura es orientativa.

## 7. Flujo de cada lote

1. Revisar `generados/handoff.md` y `generados/horarios.md`: cobertura, pendientes y mejores franjas.
2. Elegir de 10 a 11 estudios para los 30 días siguientes, con variedad de temas, formatos y regiones. Cotejarlos y registrarlos como `S-xxx`.
3. Redactar las piezas `P-xxx` con fecha, hora, título, cuerpo, estudios y tarjeta (`rotulo`, `cifra`, `frase`).
4. `python3 herramientas/difusion.py cerrar`, para validar y regenerar el lote, las piezas, las tarjetas, el calendario, los horarios, los pendientes y el handoff.
5. `python3 herramientas/difusion.py cotejo`. Si devuelve observaciones, esa pieza no sale hasta resolverlas o retirar la cita.
6. Leer cada pieza completa en `generados/lote.md`, como la leería un colega en el teléfono.
7. Commit del registro y de los generados.

Cada jueves, la rutina de cierre incluye este registro: métricas de las piezas publicadas, registros nuevos o superados, `cerrar` y commit.

## 8. Lo que nunca va

- El nombre de una institución en la firma; firma solo la Red.
- Cifras sin respaldo en los `hallazgos` del estudio.
- Lenguaje de venta, urgencia o promesas terapéuticas.
- Etiquetas diagnósticas usadas para estigmatizar, o comparaciones descalificadoras entre escuelas.
