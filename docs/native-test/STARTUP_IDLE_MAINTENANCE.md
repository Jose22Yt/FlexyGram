# Native Test — mantenimiento fuera del arranque crítico

Continuación del commit `a4a3e551`, sobre
`codex/flexygram-native-clean-bubbles`. Estos cambios están en el código fuente:
no se genera una APK ni se inicia GitHub Actions en esta entrega. La numeración
se conserva hasta preparar la siguiente compilación.

## Trabajo eliminado o reordenado

- Native Test abre `nkmrcfg` y `mainconfig` al principio de `Application.onCreate`,
  antes de `AndroidUtilities`/JNI. Solo solicita los objetos SharedPreferences;
  no invoca getters ni espera sus valores. Esto permite iniciar la lectura XML
  asíncrona de Android mientras avanza la inicialización nativa. No se crean
  hilos propios ni se precargan todas las cuentas. El beneficio depende de la
  caché de disco y del comportamiento del dispositivo.
- Se elimina la configuración especulativa de osmdroid en **todos los arranques**.
  El proveedor se configura bajo demanda, de forma sincronizada, antes del primer
  `MapView`, tanto por `initializeMaps` como por la construcción de la vista. Se
  conservan user agent y rutas de caché. Antes la preparación en globalQueue
  podía competir con la apertura o terminar después de crear un mapa.
- En Native Test, reparación de alias del launcher y calentamiento de filtros de
  enlaces e indicadores dejan de arrancar desde Application. Esperan contenido
  utilizable dibujado y una oportunidad idle del hilo principal. La Activity
  solo despacha trabajo a la cola existente; las comprobaciones de preferencias
  y carga de clases de los calentamientos también quedan en el worker.
- La señal de listo es la existente: Activity reanudada, sin bloqueo de contraseña,
  fragmento visible y medido; para chats/listas, carga inicial completada. No es
  solo el primer fondo dibujado. La comprobación de emojis y reglas de vista
  previa comparte esta espera en Native Test.
- La compuerta es de una sola ejecución por Activity, sin timers, polling ni
  invalidaciones forzadas. Revalida el estado al llegar a idle. Si se pausa o
  bloquea la pantalla antes, espera un dibujo natural posterior. `onDestroy`
  retira el IdleHandler; recrear la Activity no repite los tres calentamientos
  de proceso. Puede no haber calentamiento si nunca se llega a una pantalla
  utilizable: son cachés opcionales con carga bajo demanda, no recuperación de
  notificaciones.
- `NaConfig` deja de guardar de nuevo `showRPCError=false` cuando ya vale false.
  Mantiene la desactivación si estaba habilitado y los logs están desactivados.
- Recargar NekoConfig con `force=true` ya no añade otros cinco centros de datos.
  Conserva la identidad y el estado de los cinco existentes.

Autenticación, mensajes pendientes, push, SQLite, cuentas, plugins y rotación de
proxy conservan su inicialización. Las preferencias visuales y sus migraciones
siguen cargándose antes de construir la interfaz: aplazarlas indiscriminadamente
mostraría valores predeterminados incorrectos.

## Medición y límites

Las secciones `Flexy.startup.preference_prefetch`,
`Flexy.startup.launcher_repair`, `Flexy.startup.link_warmup` y
`Flexy.startup.loader_warmup` permiten localizar prefetched preferences y
**despacho** de calentamientos en una traza. Los dos últimos métodos pueden
encolar la construcción real del caché en otro trabajo de globalQueue; estas
secciones no representan su costo total ni miden la mejora de apertura.

No hay Android conectado ni cuenta de laboratorio. No se afirman porcentajes,
FPS ni milisegundos ahorrados. Los perfiles Baseline/Startup propios siguen
pendientes de captura real; esta entrega tampoco los inventa.

En dispositivo, comparar con el mismo APK base, estado de compilación ART y datos:
arranque frío/caliente, tiempo hasta lista utilizable, primer toque y frames de
los primeros segundos. Probar además entrada desde notificación, app bloqueada,
rotación antes de completar la carga, mapas con caché limpia, limpieza de enlaces,
cambio de icono y recarga repetida de ajustes. Usar el laboratorio existente de
`performance` y Perfetto; distinguir red de lectura local.

## Validación de host

Los tests ejecutan las clases reales de compuerta idle y los métodos reales de
planificación/configuración con dobles de Android: contenido todavía cargando,
eventos repetidos, pausa entre dibujo e idle, callback obsoleto tras destrucción,
recreación, exclusión concurrente por proceso y configuración de mapas antes de
crear su vista. Son pruebas de corrección y orden, no benchmarks de un teléfono.

Resultado final de host: **549 passed, 41 skipped** en la suite completa, con
R8 real habilitado para sus fixtures; **11 passed** en la comprobación focalizada
final. `StartupIdleWork` también se compiló contra las clases Android reales y
se comprobó la interfaz de osmdroid 6.1.20. Sintaxis de los Java modificados y
`git diff --check` correctos. No equivalen a una compilación completa de APK,
una ejecución en Android ni una medición comparativa de rendimiento.
