# beta72: presión de memoria y retorno a la app

Base 3f77b11aa35f388d52ceed477f5e5b1ff8aa49a4; versión
1.0.0-beta.72-memory-policy, código 1361. Misma base nativa optimizada y paquete.

## Hallazgo verificado

ApplicationLoader.onTrimMemory trataba UI_HIDDEN (20) como presión de memoria.
En cada ocultación vaciaba imágenes pequeñas, imágenes generales y animaciones,
además de las cachés auxiliares de métricas, blur e historial. Volver podía requerir
repetir lecturas/decodificaciones aunque el proceso siguiera vivo. La regresión
sobre el callback real falla antes de la corrección: 10000 avisos de ocultación
provocan vaciados e incluso pueden inicializar ImageLoader solo para limpiarlo.

Había además una asimetría: RUNNING_LOW (10) y RUNNING_CRITICAL (15) no vaciaban las
cachés de imágenes, mientras UI_HIDDEN sí; clearMemory omitía wallpaperMemCache e
inu_strippedCache. Son defectos concretos de política de recursos. No demuestran
por sí solos la causa completa de la degradación que el usuario nota tras horas.

## Cambio

- UI_HIDDEN ya no dispara limpieza de estas cachés. Las vistas/recursos ópticos
  mantienen su liberación por ciclo de vida; se conserva el arreglo del dock beta71.
- RUNNING_LOW reduce cada caché de imágenes hasta un objetivo de la mitad de su ocupación,
  conservando las entradas recientes según su orden existente. Se reutiliza el
  algoritmo LRU y sus callbacks de liberación, sin cambiar el límite normal.
- RUNNING_CRITICAL, los niveles de presión de fondo y onLowMemory liberan las
  cinco cachés: imágenes pequeñas, generales, animaciones, fondos y miniaturas.
- Un aviso de memoria no construye ImageLoader si aún no existía. Se conservan
  las comprobaciones nativas de uso de bitmaps/animaciones al expulsar entradas.

No se borran archivos, datos, mensajes ni cuentas. No se fuerza GC, se reinicia el
proceso ni se añade un temporizador de limpieza. No se toca SQLite, ordenación de
chats, sincronización, animaciones o shaders. Los límites de imágenes no aumentan.
Retener cachés acotadas favorece el retorno en caliente, a cambio de conservar más
memoria que el vaciado total anterior cuando se oculta la interfaz; bajo presión
se libera de forma graduada. No se promete que Android conserve el proceso.

## Revisión de acumulación

En las cachés personalizadas examinadas ya existen límites: métricas de texto
32 entradas/32768 caracteres, historial anticipado 2 entradas/512 KiB de payload
serializado (no tamaño de heap) con TTL de 5 s, y blur de fondo 2 entradas con
imagen reducida a un máximo de 384 px por lado mayor. Eso no descarta fugas en
otras rutas ni sustituye inspeccionar un heap de una sesión larga.

## Verificación

Se ejecutan los callbacks reales de ApplicationLoader en un host JVM explícito y
los cuerpos reales de trimMemory/clearMemory con el LruCache de producción. Se
comprueban 10000 ocultaciones sin limpieza y 1000 ciclos de llenado, presión baja
y crítica: 8 entradas pasan a 4 y después a 0, la entrada promovida reciente se
conserva y el presupuesto sigue siendo 8. Se verifica también el cargador ausente,
onLowMemory y la ausencia de alteraciones por RUNNING_MODERATE. Son comprobaciones
de comportamiento y ocupación, no tiempos de GPU, FPS ni memoria de bitmaps reales.

Suite general: 549 pruebas pasadas y 41 omitidas en este entorno. Tras revisar
el caso de miniaturas estáticas con ImageLoader ausente, la comprobación específica
final también pasa (2 pruebas). Ese caso libera la caché estática sin inicializar
el cargador. No se repite el harness Compose: no cambian sus fuentes ni ciclo de vida.

Revisión final: aprobado para compilación; aceptación física y sesión larga pendientes.

## Medición pendiente de la degradación prolongada

Comparar después de la sincronización inicial, con el mismo tema, chats y opciones,
en t0 y después de 30/60/120 minutos de uso equivalente. Registrar PID, PSS/heap,
GC, frames y temperatura; comparar volver al mismo proceso por separado de un
arranque con proceso nuevo. Un crecimiento inicial de caché que se estabiliza no
prueba una fuga. No usar un umbral fijo de 16,6 ms en todas las tasas de refresco.

Capturas de diagnóstico de solo lectura en un equipo con ADB:

```sh
adb shell pidof com.flexygram.messenger.nativebaseline
adb shell dumpsys meminfo com.flexygram.messenger.nativebaseline
adb shell dumpsys gfxinfo com.flexygram.messenger.nativebaseline framestats
adb shell dumpsys thermalservice
```

Si el proceso vuelve a ser rápido al forzar detención sin borrar datos, priorizar
heap retenido, colas/listeners y trabajo en segundo plano. Si sigue lento con PID
nuevo, priorizar perfiles de arranque, almacenamiento/consultas y sincronización.
El comportamiento del teléfono se ha solicitado al usuario sin bloquear esta
corrección. No hay una medición prolongada ni un dispositivo conectado en este entorno.
