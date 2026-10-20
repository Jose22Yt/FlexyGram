# Work2 — navegación, lifecycle y productor beta

FlexyGram1.0, creado y dirigido por @Lukhou23. Continuación de PR23 desde
`40c80878b18cdc50f49d44eb4fb26a31b9b0cf6a`. Código cliente, no infraestructura.
PR24/Work1 observado en `db5b9a113d54f552a925ea233c5b199ab95bfcdb`.

## Correcciones reales

1. **NotificationCenter**: incorporada exactamente la línea revisada de
   `ca5c9bba9b5e0229fd452da255ed0921d4a88ce0`. La tarea reprogramada ahora ejecuta
   el método de expiración y conserva su referencia cancelable. Umbrales intactos.
   Su regresión original se copia sin cambios a `tests/beta_development/`, sin
   modificar el directorio de herramientas/pruebas de Work1.
2. **Atrás durante apertura**: el método Activity anterior enviaba el cierre mientras
   ActionBarLayout lo rechazaba por transición activa; el cierre se perdía. El arnés
   ejecuta el método anterior real y reproduce `BACK_DURING_OPEN_WAS_LOST`.
   Ahora el hardware Back y la flecha pasan por la misma cola acotada de intenciones.
   Esperan transición/gesto y conservan la última petición, sin apagar las animaciones.
3. **Python al reconstruir Ajustes**: el callback anterior retenía la celda creada al
   pulsar; una vista nueva por cambio de tema perdía estado y resultado. El arnés ejecuta
   ambas Activities reales con dobles y reproduce `REBUILT_PROBE_LOST_PENDING_STATE`.
   ProbeState vive en Activity, las vistas nuevas leen su estado y el resultado actualiza
   la celda vigente. Worker usa contexto Application y referencia débil al propietario,
   sin retener la celda/Activity durante inicialización; cierre invalida resultados.

Se mantiene el arreglo anterior de callbacks en ActionBarLayout, byte a byte.
No se cambia código común de animaciones, duraciones, curvas o diseño. Las rutas
siguen usando DialogCell, ThemePreviewMessagesCell, TextSettingsCell y Theme reales,
con conversación sintética y sin cuenta. Los temas también pasan por la cola;
la última intención explícita sustituye a otra pendiente. No se fuerza la cancelación
de un Animator nativo activo sin evidencia de que sea seguro.

## Eventos: implementación cliente del contrato Work1 v1

Sólo `src/betaDevelopment`; sin hooks globales, Logcat, textos, argumentos de navegación,
IDs de conversaciones/usuarios, URLs, tokens ni identificadores del dispositivo.

- NavigationEvents emite exactamente id/op/phase/timestamp_ns/clock. IDs opacos ASCII
  por ejecución; reloj `System.nanoTime`, `android_monotonic_ns`.
- Operaciones: startup, chat_open, chat_close, rapid_tap, transition_interrupt,
  theme_light/theme_dark. rapid_tap identifica solicitudes de la ruta separadas como
  máximo250ms, **no** eventos físicos de touchscreen ni FPS.
- Cola SPSC de4096 registros, sin locks/escritura/espera de I/O en productor UI.
  Saturación/reloj regresivo/escritura fallida incrementan pérdida, nunca se fijan a0.
  Se rechaza exportar desde el hilo productor o consumir desde dos exportadores.
- `accepted` de apertura depende del retorno true de presentFragment. Para cierre,
  se observa onTransitionAnimationStart(false,true), no el retorno de finishFragment,
  que puede ser true aunque el layout rechace el cierre. Tema exige aplicación real.
- Endpoint **`beta_idle_predraw_frame_v1`**: escena y vista siguen siendo las esperadas,
  transición/gesto inactivos, vista adjunta/visible/con foco y tamaño, pre-draw seguido
  de callback de frame. Las consultas del observador son getters sin forzar fin de
  animación. Esto **no mide presentación física, GPU completa ni input-to-photon**.
- Se cancela una petición pendiente cuando otra la sustituye; transition_interrupt
  registra esa cancelación lógica observable. No declara cancelada una animación
  nativa que sigue ejecutándose. Duplicados de callback no emiten dos terminaciones.
- Deadline del observador5s => timeout; no significa ANR. Pausa, destrucción, escena
  sustituida o invalidación antes del endpoint dejan la operación **incomplete** en el
  flujo y aumentan observer_abandoned_operations, sin inventar presented/cancelled/timeout.
  El analizador de Work1 rechaza comparaciones con estas observaciones incompletas.

### Exportación local, sin nuevo collector

Ajustes incluye «Local observations»: serializa en un executor existente, nunca en UI.
Archivos privados de la aplicación bajo `files/beta-observer/<IDopaco>_<exportId>/`:
`events.jsonl` y `observer.json`. Carpeta `.partial` = incompleta, nunca éxito.
No sobrescribe lotes anteriores ni utiliza almacenamiento compartido, red o backups.
observer.json incluye sesión opaca, export_id, número de registros, pérdidas acumuladas,
operaciones abandonadas y endpoint. No sustituye los metadatos del laboratorio de Work1.

Para analizar una ejecución, **concatenar todos sus lotes events.jsonl completos en
orden numérico de export_id**, no mezclar ejecuciones. Un ID puede empezar en un lote
 y terminar en otro; analizar sólo el segundo puede producir ORPHAN_EVENT y debe fallar.
Una captura parcial/incompleta, pérdidas>0 o lotes ausentes no acredita rendimiento.
La extracción read-only futura corresponde al collector/operador autorizado de Work1;
no se implementa otro ADB runner ni se ejecutó extracción Android.

Settings no tiene operación propia en el protocolo v1: su navegación se mantiene,
pero no se etiqueta falsamente como chat_open/startup. Para medirla hará falta revisar
con Work1 una extensión de protocolo, sin sobrescribir #24. Su analizador actual acepta
el endpoint nuevo en metadatos; una comparación requiere el mismo endpoint/fixture en
ambos clientes. No equiparar estas rutas sintéticas con conversaciones autenticadas.

## Validación ejecutada

**20/20 métodos distintos PASS** normal y `-O`, CPython3.11.17/JDK21. Cero skips,
errores o fallos finales; no sumar ambas modalidades ni las367 de PR17/85 de PR24.
Incluye las6 pruebas previas beta,1 regresión adoptada y13 métodos nuevos.

- Métodos originales/corregidos reales: expiración, callback de animación y Back.
- Activities anterior/nueva y todos los wrappers beta compilados con javac y dobles
  Android/cliente explícitos; reproducción de reconstrucción mientras Python está pendiente.
  **No es compilación contra todo el SDK/dependencias ni ejecución ART/Android**.
- Java real: cola, reentrada, pausa/cierre, temas, estado de probe, overflow, consumidor
  simultáneo rechazado y productor que continúa con escritor bloqueado sintéticamente.
- Observer real con dobles View: pre-draw/frame, invalidación, cancelación, deadline y
  supresión de duplicados. No se presentan tiempos sintéticos como métricas Android.
- Interoperabilidad: se carga read-only el analizador exacto de Work1 desde Git; acepta
  JSONL real del productor Java y endpoint/metadata sintéticos; distingue incomplete y
  cancelación. No se copiaron ni modificaron sus analizadores/verificadores.
- Políticas Diagnostic/Production/contrato histórico comparados byte a byte por las
  regresiones existentes. JNI, manifiestos, dependencias y permisos no se modifican.

Comandos (mismas variables JAVA_HOME/FLEXYGRAM_GRADLE_HOME/FLEXYGRAM_CMAKE de README):

```sh
python3.11 -B -m unittest discover -s tests/beta_development -v
python3.11 -B -O -m unittest discover -s tests/beta_development -v
```

Para interoperabilidad se necesita el objeto Git `db5b9a1…`; no hay descarga de red
 desde el caso de prueba. [IDs, hashes, logs y límites](evidence-client-navigation/results.json).
El primer error CMake se debió al header de plantilla ausente en checkout sparse:
se recuperó el archivo fijado, sin cambiar CMake ni relajar pruebas. También se conserva
el error de compilación inicial del nuevo observador, corregido antes del resultado final.

## Compilación/recursos pendientes y coordinación

**No nueva APK ni build Gradle Android en esta ejecución.** La condición del usuario
impide crear otro binario sin conservación segura del anterior confirmada por Work1.
El mantenimiento automático podó el workspace anterior antes de esta sesión. No se
borró/sobrescribió ningún artefacto o respaldo por esta tarea; no se intentó resolver403,
recuperar binarios, descargar SDK/imágenes, repetir namespaces o modificar herramientas
que están a cargo de Work1. Se recuperaron fuentes y herramientas host para desarrollar.

Se necesita de Work1: recibo de custodia/recuperación del APK beta anterior `98de3527…`,
y confirmación del contrato/endpoint para colección read-only futura. Después: build
ARM64 unsigned en ruta nueva, JNI/Chaquopy reales, revisión por sus verificadores,
conservación privada y comparación separada de hashes, sin repinar el contrato histórico.
Instalación/firma todavía requieren laboratorio y autorización independiente.

No hay pruebas Android, JNI/Python real en dispositivo, mediciones de latencia/FPS,
servicios externos o autenticación. No cambios main/develop/PR17/PR24, Actions, Production
ni Paso4. Todo queda en PR23 en borrador para revisión.
