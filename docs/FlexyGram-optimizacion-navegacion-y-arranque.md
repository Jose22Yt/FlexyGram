# Arranque e interacción durante transiciones

## Navegación

El primer `ACTION_DOWN` finaliza la transición decorativa de apertura/cierre antes
de que Android decida qué vista recibe el toque. El evento original sigue después
por el despacho nativo: no se duplica ni se sintetiza otro toque. Se sustituye la
restricción anterior a filas expuestas de la lista de chats por este comportamiento
general del contenedor de navegación, incluidos los ajustes y las capas nativas.

Presentar/cerrar un fragmento, el botón Atrás y el inicio del gesto Atrás también
pueden terminar una transición pendiente. Los gestos todavía bajo el dedo y las
ventanas modales mantienen su dueño original. Un gesto ya liberado puede completar
su animación de asentamiento antes de la siguiente interacción.

La finalización separa los animadores y los callbacks pendientes antes de cancelar,
restaura las transformaciones y libera las capas temporales. Solo completa los
callbacks capturados: un callback que abra otra pantalla no pierde su animación
nueva. Se conserva el cierre nativo de los fragmentos y su ciclo de vida.

La interrupción no espera la duración configurada del animador. No modifica las
escalas del teléfono ni las preferencias de accesibilidad. Los indicadores de
ocupación se asignan antes de iniciar la animación de retroceso, también cuando
esta termina inmediatamente.

## Arranque y carga local

- En una apertura con interfaz, los servicios auxiliares de cuentas se reparten
  entre oportunidades de renderizado. Conservan Contacts/Download para las cuentas
  activas, la reconciliación de la cuenta cero y la conexión de facturación.
- Las entradas en segundo plano conservan la inicialización inmediata; no esperan
  un fotograma de una Activity.
- La petición nativa de diálogos desde la caché se encola antes que las peticiones
  auxiliares de notificaciones y sugerencias. Se mantiene la carga anticipada de
  la cuenta seleccionada y el tamaño original de página.
- No se oculta «Actualizando» ni se omite la sincronización. Ese estado puede
  seguir apareciendo cuando Telegram realmente necesita actualizar la cuenta.

## Burbujas y desplazamiento

La animación de pulsación deja de invalidar explícitamente todo el padre: calcula
una región que cubre el mensaje y su expansión visual. Se conservan los springs
nativos y su velocidad al transferir la pulsación a la selección. La entrada
descarta antes su cola final casi asentada; el cierre libera el dueño antes de
ejecutar callbacks, evitando limpiezas duplicadas o reentrantes.

No se reducen los mensajes cargados ni se desactivan imágenes, GIF, efectos o
servicios para obtener una apariencia artificialmente más rápida.

## Evidencia y límites

- Suite general: **241 aprobadas, 31 omisiones opcionales**.
- Pruebas Android aisladas: **4 aprobadas**, con `FrameLayout`, botones y eventos
  táctiles Android reales. Comprueban el mismo toque tras apertura/cierre,
  cancelaciones reentrantes, preservación del dueño modal/gestual y la región
  invalidada por una pulsación.
- Los métodos de navegación se extraen sin cambios del código de producción. El
  anfitrión de la pila de fragmentos y el adaptador de cancelación de springs son
  dobles explícitos: estas pruebas no ejecutan `LaunchActivity` completa.
- Las pruebas JVM ejecutan el reparto por fotogramas de los servicios y la física
  real de pulsación/selección, incluida la finalización reentrante.
- No se genera APK ni se presentan tiempos de arranque/FPS medidos en un teléfono.
  Queda validar arranque frío/caliente, scroll, navegación rápida y escalas de
  animación 0,5×/5×/6× en un dispositivo.

Reproducción de la prueba Android aislada:

```bash
MAVEN_REPO_LOCAL=/tmp/flexy-m2 python tools/navigation/android/run.py \
  --sdk-root /path/to/android-sdk --output-dir /tmp/flexy-navigation-probe
```
