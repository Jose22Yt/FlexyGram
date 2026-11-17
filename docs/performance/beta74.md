# beta74: auditoría ampliada del cliente y uso prolongado

Base 349bd2dbc0e6f2d6ccf6588e3b442ef667c50520; versión
1.0.0-beta.74-client-lifetime, código 1363. Se mantiene la base nativa optimizada,
su paquete, las opciones actuales y las correcciones beta71–73. La compilación
beta73 terminó correctamente en GitHub antes de comenzar esta revisión.

## Cobertura real

Se inventariaron y leyeron para búsqueda de candidatos 12155 archivos rastreados:
2966 Java, 64 Kotlin, 6459 C/C++/cabeceras, 155 Python, 6 JavaScript y 2505 XML.
El manifiesto y los límites están en [beta74-inventory.json](beta74-inventory.json).
`tools/client_audit/inventory.py` permite repetir el inventario sin mutar la app.
Los patrones son candidatos para lectura contextual, no diagnósticos ni defectos
confirmados. No aparecieron marcadores de conflicto en el alcance escaneado.

**Esto no equivale a revisar semánticamente cada línea.** Se excluye el contenido
interno de 14 submódulos, además de código generado/no rastreado. No se certifica
seguridad criptográfica, ausencia de fugas ni fluidez universal por ese recuento.

| Área | Lectura focal / comprobación | Resultado y límite |
| --- | --- | --- |
| Arranque y ciclo de vida | ApplicationLoader, StartupAccounts, rutas de MainTabs | Se conservan carga local prioritaria y liberación del dock; se amplía respuesta a presión de memoria. |
| Recursos gráficos compartidos | AnimatedEmojiDrawable: make, attach, cleanup, updateAll | Dos defectos reproducidos y corregidos; cacheo reciente y propietarios activos conservados. |
| Multimedia | PhotoViewer: velocidad y compresión; sitios de recuperación GC | Eliminadas escrituras síncronas en esos controles; no se cambian decodificadores, formato ni contenido del video. |
| Voz / recursos nativos | VoskTranscriber: obtención, uso, cierre y callbacks | Corregido cierre concurrente, admisión de trabajos y entrega repetida de callbacks. JNI real solo se verifica por tipos; reconocimiento físico pendiente. |
| Descargas y temporales | VoskManager: HTTP, extracción, publicación y borrado | Cancelación activa, límite de espera de lectura, limpieza y coordinación con modelo en uso. |
| Ajustes | VoskSettingsActivity, observadores de iconos y rutas de configuración | Tamaños fuera del hilo de interfaz, callbacks de finalización sin retener la pantalla; no se reactivan funciones retiradas. |
| Datos y navegación | UserConfig y rutas de carga/preparación de peers | Se conservan marcadores beta73, orden de SQLite y gate de navegación; quedan rutas heredadas para perfilar. |
| Red general | ProxyPingController, fronteras de ConnectionsManager | Muestreo y barrido de candidatos; no se reescribe MTProto ni se declara auditado todo el transporte. |
| Notificaciones | Ciclo de observadores y cancelación de IDs; suite existente | Muestreo sin parche nuevo; pruebas de entrega reales en segundo plano pendientes. |
| Archivos/exportación | FlexyStickerExport y sus pruebas; inventario de fuentes retiradas | No se cambia el transporte ni se recuperan FlexyFiles/Studio; SAF físico no certificado. |
| Cámara, visor, diagnóstico | Reintentos acotados y puntos de GC explícito | Los cinco candidatos GC pertenecen a recuperación/depuración; no se eliminan indiscriminadamente ni se añade GC forzado. |
| C++/JNI, Python y recursos | Inventario estático + límites de submódulos | Compilación e integración no equivalen a auditoría profunda; ASan, heap/CPU y pruebas físicas pendientes. |

## Defectos corregidos

### P2: acumulación de emojis al desplazarse continuamente

Cada separación de un drawable cancelaba la limpieza y volvía a programarla a
cinco segundos. Una secuencia continua podía impedir que se ejecutara nunca.
Además, updateAll eliminaba entradas avanzando el índice y saltaba la siguiente.

Ahora hay un callback coalescido; otras separaciones no aplazan su plazo. Se
registra el momento de separación y se mantiene al menos la ventana cálida de
cinco segundos. La limpieza por lotes retira entradas vencidas; solo vuelve a
programarse si quedan entradas separadas dentro de esa ventana. Al cesar el
trabajo pendiente se detiene. También se cubren entradas creadas sin adjuntarse.

Se recogen primero las claves que se van a retirar, evitando lecturas indexadas
que compacten LongSparseArray tras cada eliminación. Los drawables adjuntos o
precargados mantienen sus propietarios; no se reciclan bitmaps vivos ni se fuerza
GC. Ante presión real de memoria se retiran inmediatamente los no utilizados.

La prueba reproduce el defecto anterior y simula 100000 separaciones cada 100 ms
(2 h 46 min 40 s de reloj simulado). Con ese ritmo y un propietario activo, el host
no supera el límite comprobado de 103 entradas, y después de terminar se queda
solo el propietario activo, sin callbacks pendientes. **103 no es un límite global
de producción**: el volumen real depende de propietarios activos y del trabajo
reciente. No es una medición de heap, GPU, batería ni horas físicas de teléfono.

### P1: modelo de voz cerrado durante reconocimiento

Cambiar el idioma podía cerrar Model desde la interfaz mientras el trabajador aún
lo usaba. Los monitores de obtainModel/releaseModel no protegían todo el periodo
del Recognizer. La regresión anterior detecta el cierre durante una tarea activa.

Obtención, reconocimiento, cierre, reemplazo y borrado ahora comparten el ejecutor
propietario. El cierre no se ejecuta en la interfaz ni dentro de un reconocimiento.
Las peticiones de liberación se coalescen. La presión de memoria también puede
liberar el modelo, después del trabajo que lo usa; no inicializa un modelo jamás
utilizado. Cambiar/borrar un idioma no cierra innecesariamente otro modelo.

Se admiten como máximo cuatro transcripciones pesadas, incluida la activa.
El exceso recibe un error explícito, sin retener una cola ilimitada de audios y
callbacks. Un callback que lanza una excepción de aplicación ya no se invoca una
segunda vez. El trabajador usa prioridad de segundo plano. No hay temporizador
que fuerce la liberación de un modelo actualmente en uso.

### P2: cancelación, tamaños y temporales de modelos

La bandera de cancelación anterior no interrumpía read() bloqueado con timeout
infinito. Se cancela el Call real de OkHttp y se establece un timeout de lectura
de 30 s sin datos; no se impone ese límite a la duración total de un modelo grande.
El inicio/cancelación son coordinados y se evita descargar otra vez un instalado.

Archive y staging se limpian en finally ante fallo o cancelación. La extracción
comprueba cancelación también dentro de cada archivo y conserva la validación de
rutas. Publicar o borrar archivos espera al propietario del modelo, fuera de la
interfaz. Cancelar una publicación que espera a un reconocimiento no interrumpe
ese reconocimiento: la cancelación se comprueba antes de publicar. Esa fase puede
esperar a que termine el trabajo activo.

installedSize recorría todo el directorio al vincular filas. Ahora usa una lectura
asíncrona coalescida y caché invalidada con generación, para no publicar resultados
anteriores a una instalación/borrado. Mientras se borra se muestra el estado localizado de carga y se impide
seleccionar/descargar ese modelo; peticiones repetidas no añaden otra eliminación.
La finalización libera ese estado y actualiza la fila sin retener la pantalla.
La fila de tamaño muestra el recurso localizado
«CalculatingSize» mientras espera. Este evento no usa onFinished, que selecciona
un idioma: actualizar el tamaño no cambia el idioma elegido. Los observadores se
recorren sobre un snapshot y pueden retirarse sin saltar al siguiente.

### P2: escrituras durante los controles de video

PhotoViewer hacía commit en cada variación del selector de velocidad. Ahora los
reproductores reciben la previsualización durante el gesto y solo se persiste al
confirmar; la confirmación funciona aunque el último valor coincida con el último
preview. Botones y selección de Cast ya emiten confirmación. La compresión también
usa apply y evita escrituras idénticas, conservando actualización y preview nativos.

## Verificación

- Suite general final: 558 pruebas pasadas, 41 omitidas por el entorno.
- Revisión final focal tras reforzar la coordinación del callback de emojis:
  10 pruebas pasadas. Las regresiones de medios, modelo y emojis fallan antes y pasan
  después; cancelación/tamaños también fallan al ejecutar el código de beta73.
- Compilación Java de las fuentes reales VoskManager/Transcriber/Model/Models contra
  SDK Android 37, Vosk 0.3.75, JNA 5.18.1 y OkHttp 5.5.0: correcta. APIs de la app
  no relacionadas se representan explícitamente; no es compilación de toda la APK.
- Prueba con VoskManager real compilado y OkHttp real: una respuesta HTTP local
  detenida tras el primer byte se interrumpe al cancelar. No es una medición de red móvil.
- ZIP real y archivos temporales JVM: éxito, checksum erróneo, fallo de lectura,
  cancelación antes/durante extracción y ruta fuera del staging; limpieza verificada.
- Native Vosk y MediaCodec se sustituyen por hosts en las pruebas de concurrencia.
  No se afirma haber probado reconocimiento real, cámara o reproducción física.
- Diff sin errores de formato; APK y validación física pendientes de CI/dispositivo.

## Uso prolongado: qué queda por demostrar

El cliente elimina esas acumulaciones por sus eventos y por presión de memoria;
no se añade un limpiador global periódico, reinicio automático ni borrado de datos.
No se promete velocidad idéntica bajo cualquier carga, plugins, temperatura o estado
de Android. Estas correcciones no prueban por sí solas toda la causa del teléfono.

Comparar t0 tras sincronizar y t30/t60/t120 con el mismo contenido/opciones: PID,
PSS/heap, objetos retenidos, pausas GC, frames según tasa real de pantalla, temperatura
y tiempo hasta lista/chat visible. Separar regreso al mismo proceso y proceso nuevo;
no reinstalar ni vaciar caché entre muestras. Si la lentitud persiste tras terminar
el proceso, revisar almacenamiento, consultas, sincronización y perfiles de arranque.

Pendientes: heap físico después de uso largo, cachés de metadatos de documentos de
emoji, hooks de plugins, entradas de navegación fuera del gate normal, decodificadores
sin progreso, notificaciones/cámara en dispositivo y contenido interno de submódulos.
Esos pendientes no se convierten en causas confirmadas sin reproducción/perfil.

**Revisión del parche: aprobado para compilación. La auditoría integral y la
aceptación de rendimiento en teléfono permanecen abiertas.**
