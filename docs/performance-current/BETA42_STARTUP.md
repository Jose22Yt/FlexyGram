# Beta 42 — arranque, tareas auxiliares y actualizaciones pendientes

Base: `c68627aba75861f4a9d3fac611f810406845344d`, beta 41/build 1330. La revisión actual prepara **beta 42/build 1331** en `codex/flexygram-beta-glass`. **No se compila una APK con estos cambios**; los commits utilizan `[skip ci]`.

## Cambios

1. **Cuenta visible antes de las sesiones secundarias.** Se siguen cargando las configuraciones de todas las cuentas y la cuenta cero conserva su prioridad por las preferencias globales. Al entrar por la interfaz, únicamente cero y la seleccionada preparan sus controladores antes del contenido; las otras sesiones activas aprovechan la cola existente de servicios, una por frame. La solicitud SQLite de los diálogos locales seleccionados conserva su ruta nativa. Los accesos iniciales sin interfaz mantienen la preparación inmediata; una entrada de servicio posterior a un inicio UI solicita al hilo principal que complete las sesiones pendientes sin esperar otro frame; las peticiones simultáneas comparten un único trabajo encolado. Si una cuenta cierra sesión mientras espera, su marca se limpia sin iniciar sus controladores.
2. **Registro de galería fuera del hilo principal.** Las cuatro llamadas binder a `ContentResolver.registerContentObserver` del constructor de `MediaController` pasan a `Utilities.globalQueue`, después de preparar sus campos. Cada fallo de permisos/proveedor sigue aislado y se intentan los demás registros. Los callbacks de galería conservan su ruta existente; no se mueve la vigilancia de capturas de pantalla de `startMediaObserver`. La suscripción global a `playerDidStartPlaying` se realiza una vez, en lugar de repetir la misma llamada dentro de las diez cuentas.
3. **Ping de proxy sin despertares cuando está apagado.** Antes existía un callback cada diez segundos aunque no hubiera proxy. El controlador se registra una vez, tras la carga de las configuraciones/cuentas, y observa `proxySettingsChanged`. Solo programa el siguiente ping si hay un proxy habilitado y seleccionado; desactivarlo o quitarlo cancela el callback. Con proxy activo conserva el intervalo, la cuenta seleccionada y las notificaciones de resultados. La primera comprobación se pospone al intervalo habitual y solo lee antes el indicador de configuración ya disponible; no adelanta la decodificación de la lista guardada al arranque.
4. **Tabla de iconos sin 1.566 objetos Entry.** El importador genera registros `long` con IDs y metadatos compactos, más los catálogos primitivos de recursos/colores. Se mantiene búsqueda binaria, ordenación válida para `R` no final, procedencia, tintes y dimensiones de los 235 originales/1.566 asociaciones. La carga de un recurso ajeno al mapa no fuerza la inicialización de preferencias de iconos. El contenido gráfico no cambia.
5. **Expiración efectiva de notificaciones durante animaciones solapadas.** `NotificationCenter.checkForExpiredNotifications` reprogramaba una lambda que solo asignaba el siguiente comprobador, sin ejecutarlo. Una retención reciente podía quedar sin una comprobación posterior y mantener trabajo de UI pendiente. Ahora se programa el comprobador real, se evita duplicarlo si un callback reentrante ya lo ha registrado y no queda un timer si ya no hay retenciones. Se conservan los umbrales y los eventos nativos de operaciones pesadas.

No se modifican la velocidad propia de las animaciones, el diseño, los efectos de vidrio/desenfoque ni las políticas de ahorro. No se trasladan controladores de mensajes o vistas a un hilo de trabajo.

## Evidencia

Suite final: **382 pruebas correctas y 39 omitidas** por corpus/dependencias opcionales no disponibles en el entorno. Generación y hashes de iconos verificados; el diff no añade errores de espacios. La revisión de sintaxis no introduce errores nuevos respecto al código base (el parser conserva una limitación con un NUL literal preexistente en MediaController).

- Regresiones Python/JVM: prioridad de la cuenta seleccionada, sesión vacía/login, cuentas secundarias, cierre de sesión durante el inicio, entrada en segundo plano, mil peticiones de servicio agrupadas en un único callback, reparto por frames y trabajo pendiente.
- Proxy: ausencia de callback al estar desactivado, inicialización idempotente, cambios repetidos de configuración, cambio de cuenta, cancelación inmediata y ejecución tardía de un callback ya obsoleto.
- Galería: las cuatro llamadas solo se ejecutan tras despachar al worker; un fallo de registro no impide los siguientes.
- Notificaciones: dos retenciones de animación de edades diferentes terminan liberándose; cancelación y reentrancia no dejan callbacks duplicados o permanentes.
- Cargador de iconos: se mantienen las pruebas de recursos, estados, caché, densidad, proporción y aislamiento de tintes. Las diez clases de iconos superan de nuevo la verificación aislada contra Android API 35 y AndroidX Core 1.15.0; no es una compilación completa API 37.

La medición [beta42-icon-map.json](beta42-icon-map.json) compara el mapa real de la base con el actual en siete JVM nuevas por caso, usando IDs `R` sintéticos no finales. La clase sintética `R` se resuelve antes de medir. Mediana de asignación inicial: **295.264 → 245.336 bytes**, una reducción de **49.928 bytes** en este recorrido. Ambos mapas asignan **0 bytes** en un millón de consultas ya calentadas. En esa microprueba la búsqueda compacta tardó más por consulta (aproximadamente 13,29 frente a 10,06 ns); se conserva la reducción de objetos de primera carga, sin afirmar una mejora general de CPU a partir de ese resultado. El tiempo de primera consulta también varía con la carga/verificación de clases.

Estas son medidas HotSpot de código de metadatos, no tiempos de arranque Android, memoria PSS, FPS ni latencia táctil del teléfono. Los originales y sus tamaños no se alteran para obtener ese resultado.

Reproducción:

```sh
python -m pytest tests/ -q -p no:cacheprovider
python tools/ios_originals/generate.py --check
python tools/performance_current/measure_icon_lookup.py --output /tmp/icon-lookup.json
```

El último comando requiere que el commit base indicado esté disponible en Git; no crea una APK.

## Comprobaciones pendientes en dispositivo

Medir arranque frío/tibio, primera pantalla utilizable y FrameTimeline con cuenta única/múltiple, entrada por notificación y cambios rápidos de cuenta. Verificar galería/adjuntos tras crear o borrar fotos, con y sin permisos, y proxy al activar/desactivar/cambiar de servidor. Comprobar apertura de conversaciones y scroll con los modos visuales actuales. Los cambios eliminan trabajo concreto y corrigen una retención, pero no certifican fluidez del 100 % en todos los dispositivos.

## APK anterior, separada de esta revisión

La compilación autorizada de la **beta 41/build 1330** terminó correctamente en [GitHub Actions 42932002424](https://github.com/Jose22Yt/FlexyGram/actions/runs/42932002424), con el código base `c68627aba75861f4a9d3fac611f810406845344d`. Las pruebas, ensamblado y verificaciones de firma/ABI del workflow pasaron.

[Descargar artefacto ZIP de la APK beta 41 ARM64 debug](https://github.com/Jose22Yt/FlexyGram/actions/runs/42932002424/artifacts/13817049184).

Se verificó además el artefacto descargado: paquete `com.flexygram.messenger`, `versionName=1.0.0-beta.41`, `versionCode=1330`, ABI `arm64-v8a`, 95.660.439 bytes. SHA-256 de la APK:

```text
473a0f9a0356fc0e5ff2ceb76555dd365ff6252c964ecae127510020d63987c7
```

Esa APK **no incluye las optimizaciones nuevas de beta 42**. No se presenta como la firma de producción custodiada por el propietario.
