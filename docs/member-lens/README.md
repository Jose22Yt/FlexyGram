# Quick Member Lens 1.0 — implementación para revisión

Base: Beta `bf96667efac14d0cbbf6677471890a366c3ef3c0`, `feat/beta-official-source-v2`. Rama independiente `feat/quick-member-lens`. El PR #170 sigue separado: no se repite su integración ni se modifica su rama. Los hunks de ChatActivity de ambas propuestas requieren revisión conjunta antes de la siguiente Beta.

## Funcionamiento implementado

1. Activar **FlexyGram → Chat → Mensajes e interacción → Filtro rápido por miembro**. El valor inicial es apagado y se guarda en las preferencias existentes de NekoConfig, clave `flexy_quick_member_lens`. Una fila directa, sin categoría ni submenú nuevos. Incluida en búsqueda/compartición de filas de los ajustes.
2. Mantener pulsado el avatar del autor de un mensaje en un grupo compatible. Aparece **Ver mensajes de este miembro** en el menú de AvatarPreviewer existente. Con esa previsualización desactivada, se ofrece un menú nativo compacto. El toque normal sigue abriendo el perfil, sin modificaciones.
3. Se presenta una consulta temporal sobre el chat original: avatar, nombre, subtítulo, Buscar y Cerrar; búsqueda textual, carga discreta, estado vacío, error y reintento. Cerrar/Atrás retira el fragmento sin tocar los mensajes ni la posición del ChatActivity que permanece debajo.
4. Los resultados utilizan ChatMessageCell original, fechas de Telegram y los MessageObject recibidos. No se reconstruye contenido a partir de texto o thumbnails simulados. Fotos, documentos, voz, stickers y otras acciones remiten al mensaje original para operar allí con sus controles completos. No se promete un segundo reproductor ni todas las acciones multimedia dentro del filtro. Los álbumes se presentan por sus mensajes individuales, sin reordenar ni inventar su contenido.
5. Tocar un resultado o **Ir al mensaje original** cierra el filtro y solicita el salto nativo al ID en el chat de origen. Ese salto es intencional: a diferencia de Cerrar, cambia la posición original para mostrar el mensaje elegido.

## Arquitectura y límites de identidad

Se extiende `FilteredSearchView` con un alcance opcional e inmutable. El camino normal conserva su API. Se reutilizan su solicitud `TL_messages_search`, respuestas, cursor `offset_id`, paginación, modelos y RecyclerListView. No se usa el singleton global de búsquedas de MediaDataController: la búsqueda de otra pantalla no se sobrescribe. No se añade un segundo protocolo/motor de búsqueda ni un filtro que simplemente oculte el historial completo.

| Dato | Procedencia y uso |
|---|---|
| Cuenta | Cuenta del fragmento de origen; permanece fijada durante la consulta |
| Grupo | `dialog_id` negativo del chat actual, nunca búsqueda global |
| Participante | `messageOwner.from_id.user_id`, ID long completo; no el autor de `fwd_from` |
| Foro/tema | Tema actual; `top_msg_id` y flag 2. En la raíz del grupo el alcance es el grupo |
| Remitente | `from_id` InputPeer y flag 1, mediante MessagesController nativo |
| Paginación | Límite nativo de 20, cursor de la última respuesta, deduplicación por ID, parada al agotarse/no avanzar |

También se comprueba que cada resultado pertenezca al grupo, remitente y tema solicitados. Una respuesta incoherente no se muestra: pasa a error/reintento. Los administradores anónimos y autores representados por canales no se convierten artificialmente en personas: no se ofrece esta acción para ellos. Se excluyen privados, canales de difusión, monoforos, búsquedas ya activas y hilos que no sean temas compatibles. Los usuarios eliminados se consultan sólo cuando existe una identidad personal expuesta y Telegram admite el InputPeer correspondiente; el servidor decide accesibilidad y mensajes conservados.

## Lifecycle y rendimiento

- No existe hilo propio, polling, observador permanente, carga de historial general ni blur nuevo. La ruta normal añade únicamente la comprobación del interruptor al mantener pulsado un avatar.
- Consulta asíncrona; vacío inicial sin demora artificial; debounce de 250 ms para texto. Un solo request del filtro en curso. Las páginas duplicadas durante carga se ignoran.
- Cambio de texto: cancelación del request previo y generación `requestIndex` nativa. Respuestas obsoletas no mutan las listas. Destrucción: cancela request/runnables, invalida generación, desconecta adapter y libera modelos/callbacks.
- Las páginas añaden filas concretas. No se reconstruye toda la lista para cada página ni se usan animaciones de entrada por fila. Las celdas e ImageReceivers se reciclan por la infraestructura original.
- Los modelos cargados viven sólo durante la consulta, igual que en el buscador original; no hay caché global adicional. Pueden crecer conforme se recorren páginas; medir consumo en consultas largas.
- La recreación de la vista del mismo fragmento conserva un snapshot de modelos/cursor/consulta y estado de layout; no vuelve a descargar todas las páginas. Se rechaza restaurar un snapshot de otra cuenta, grupo, persona, tema o texto.
- El origen se conserva mediante WeakReference. Si dejó de existir, el salto utiliza la apertura nativa del grupo/tema. Si falta el mensaje inicial del tema necesario para esa ruta, se informa un error y no se abre silenciosamente otro tema.
- No hay cambios en sesiones, preferencias de lectura, almacenamiento de mensajes, cuentas, firma, versionado o distribución.

## Preferencias y textos

Sólo `MemberLensConfig` escribe la nueva preferencia booleana, usando el store existente y `apply()`. No se copian SharedPreferences completas. No se altera la allowlist de FlexyStudio para exportarla automáticamente. Español, inglés y ruso; recursos temáticos, tamaños de texto en sp, botones de 48dp y etiquetas de accesibilidad. No se incluye información de consultas/cuentas en telemetría o ejemplos publicados.

## Verificación realizada y pendiente

Ver `results.json`. Ejecutar desde raíz:

```sh
python3 -m pytest -q tests
PYTHONPATH=tools/connected_alpha python3 -m unittest tools.connected_alpha.test_context_panel tools.connected_alpha.test_header_fusion tools.connected_alpha.test_header_portrait -v
python3 tools/settings2/checks.py
./gradlew --version
```

Los tests nuevos ejecutan el Scope real y métodos/bloques extraídos de producción para construir flags, cancelar y restaurar estado. Utilizan dobles explícitos del transporte/UI/modelos donde es necesario. **No equivalen a conectarse a Telegram, compilar Android ni verificar ChatMessageCell en pantalla.**

La sintaxis de diez archivos Java de producción se comprueba con JavaParser Java21; tampoco equivale a compilación semántica. El wrapper de Gradle 9.7.1 falla en este entorno con `Network is unreachable`; SDK37/JDK21/Maven no están preparados. No se omiten JNI/Chaquopy ni se desactivan gates para presentar una compilación válida.

El contrato heredado de Settings2 rechaza la nueva modificación de ChatActivity (11 pasan, 1 falla). Se conserva el control para revisión del nuevo alcance. El gate histórico general de distribución Beta puede rechazar esta fuente igual que los cambios posteriores a su allowlist: no se relaja desde este feature. No se declara CI completamente verde.

**Pendientes:** ejecución integrada, conexión real con Telegram usando una cuenta/grupo de pruebas, capturas reales, validación física en Poco X8 Pro Android17/HyperOS4, estados multimedia, accesibilidad, orientación, presión de memoria, cuentas cambiantes y mediciones. No se han medido FPS, latencia ni consumos. No se generan maquetas para sustituir capturas reales. El proceso completo tras muerte de proceso depende de la restauración de navegación del cliente; no se promete conservar indefinidamente un snapshot que sólo vive en memoria.

## Aceptación física requerida

- Interruptor on/off: una ubicación en Chat, valor persistente, perfil normal al tocar avatar y acciones anteriores intactas; con AvatarPreviewer activado y desactivado.
- Grupo pequeño y supergrupo con miles de mensajes: comparar IDs de dos personas y un reenviado con el filtro nativo `from:`. Sólo el remitente del mensaje dentro del grupo debe aparecer.
- Temas: misma persona en dos temas y raíz del foro; ningún cruce de resultados entre temas al filtrar uno. Administrador anónimo y enviar-como-canal no exponen identidad personal falsa.
- Consulta sin texto, con texto, vacía y error de red; reintentar primera página y páginas posteriores. Desplazarse a resultados antiguos, sin duplicados ni saltos del scroll.
- Texto largo, foto, vídeo, documentos, voz/audio, sticker/GIF, respuesta y álbum. Se muestran modelos/celdas reales y se puede ir al original para sus operaciones completas.
- Abrir, escribir, cerrar y abrir otra persona antes de recibir la respuesta. El callback antiguo no actualiza el filtro nuevo. Atrás/Cerrar devuelve exactamente el anclaje previo del chat; Ir al original salta deliberadamente al mensaje elegido.
- Claro/oscuro/tema personalizado, fuentes grandes, RTL y TalkBack. Recrear/rotar con varias páginas cargadas y con request en curso. Cambiar de cuenta debe cerrar la consulta de la cuenta anterior.
- Medir con el laboratorio `tools/connected_alpha/performance/` a la frecuencia efectiva del dispositivo, misma caché/carga/temperatura y música activa. Comprobar ausencia de actividad de Lens cuando no se usa y memoria liberada tras cerrar.

Integración: revisar PR independiente sobre la fuente Beta indicada, reconciliar con PR #170, ejecutar compilación completa y aceptar físicamente antes de modificar el pin de la próxima entrega protegida. No se fusiona main ni se publica APK. Revertir el commit retira la función; la preferencia booleana queda inerte y no requiere migración de datos.
