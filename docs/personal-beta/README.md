# Primera prueba personal offline: vía separada y pendiente de autorización

FlexyGram — responsable @Lukhou23. Esta preparación no autoriza generar claves,
firmar, entregar, instalar ni ejecutar APK. No cambia ningún contrato de laboratorio.

## Decisión técnica

**Sí es viable preparar una prueba personal de la beta offline en un teléfono ARM64
compatible**, sin esperar a que este host pueda arrancar un emulador. Viable no significa
APK lista ni funcionamiento comprobado. El objetivo inicial será abrir la interfaz local,
probar JNI/Python y navegar por fixtures; no iniciar sesión ni conversar por Telegram.

Base inspeccionada de PR23: `e50fa88e80358893d08e9901e81e3b0a74a0a54d`.
PR24 `db5b9a113d54f552a925ea233c5b199ab95bfcdb`; PR25
`2363f38ccab1618a75fec790c04b78b6067e91bc`. Esta rama sólo añade preparación/importación
host y se apila sobre PR25. No modifica código, recursos, Gradle o navegación de Work2.

PR23 mantiene `io.github.jose22yt.flexygram.beta.development`, minSdk24, target36,
API0/hash vacío y seis capacidades false en `gradle/beta-development.json` y la política
Java/JNI. Su manifiesto elimina INTERNET, backup/restauración y componentes externos.
Estas condiciones deben comprobarse de nuevo **en el binario que se entregue**; no basta
el nombre del archivo ni la inspección del fuente. No se necesita cambiar el package,
agregar INTERNET, habilitar autenticación ni desactivar políticas para probar esta UI.

Android exige firma para instalar. Una APK unsigned no se arregla activando «orígenes
desconocidos». Hace falta firma propia aprobada, custodia recuperable y verificación
posterior de certificado y contenido. No reutilizar certificados ajenos ni firma Production.

El dispositivo declarado por el responsable es Poco X8 Pro/ARM64/Android17; no se ha
consultado aquí su sistema real. La página de memoria NO se deduce del modelo ni del
nivel Android. Medir con `getconf PAGE_SIZE`; 4096 no acredita16KB. Una ejecución16KB
con modo compatibilidad activo tampoco acredita16KB estricto.

## Condiciones antes de proponer una APK concreta

Work2 debe preparar:

1. Commit revisado de PR23 y build ARM64 completo con JNI/Chaquopy, sin SKIP, que incluya
   las últimas correcciones y productor de eventos. La APK antigua98de3527… no contiene
   los cambios nuevos. Esta misión no recompila ni sustituye ese artefacto.
2. Respaldo recuperable, hash del unsigned, clases Java del mismo build, logs y evidencia
   ELF/políticas/manifest. Usar gate y verificación de respaldo de PR25; no subir binarios
   a GitHub. El gate unsigned se ejecuta ANTES de firma; no usarlo sobre un APK firmado.
3. Confirmar API0/hashvacío, seis capacidades false, sin INTERNET, sin sharedUserId,
   restauración/importación automática, componentes exportados imprevistos o servicios activos.
   Identidad y sandbox propios; no reutilizar datos de Telegram/Exteraless/otras betas.
4. Después de autorización de custodia/firma: recibo nuevo de beta con hash unsigned y
   firmado, certificado público esperado, versión, commit y chequeo de equivalencia de
   contenido/políticas con herramientas revisadas. El contrato Diagnostic histórico no sirve
   automáticamente para beta. Ajustar el verificador nuevo de beta requiere revisión propia,
   sin repinar contratos o hashes anteriores.
5. Medio de entrega privado aprobado y recuperación exacta por el responsable. Nunca
   reutilizar un hash del unsigned para identificar el firmado; serán binarios distintos.

### Bloqueo del archivo anterior, sin espera circular

`docs/beta-development/CLIENT-NAVIGATION.md` de PR23 informa que el mantenimiento podó
el workspace anterior y que no se recuperaron binarios allí. Work1 tampoco tiene APK/ZIP
originales. El403 anterior ocurrió antes de transferir. No existe evidencia nueva de que
el respaldo haya sido guardado; no se puede emitir un recibo ficticio de conservación.

Si no aparece una copia privada verificable: registrar el artefacto anterior como no
recuperado y solicitar autorización para un **nuevo build identificado por hash nuevo**,
una vez preparada una conservación viable. No exigir coincidencia imposible con el hash
viejo ni declarar perdido globalmente un archivo sólo porque no está en esta sesión.
El usuario puede custodiar artefactos y clave futura en medios privados propios con
recuperación verificada; no es obligatorio un proveedor concreto. Esta propuesta no
habilita transferencias alternativas ni elimina el403 de la vía actual.

## Autorizaciones independientes que faltan

- Aceptar una **prueba personal limitada**, separada del laboratorio aislado y sin certificar
  compatibilidad general. No cambia las puertas de Diagnostic/Production ni autoriza beta pública.
- Aprobar la custodia recuperable y, sólo después, la generación/uso de una clave propia
  para firma del build de desarrollo concreto. No mandar contraseñas o claves al chat/GitHub.
- Aprobar firma de la APK por hash/commit y su entrega privada al responsable.
- Aprobar instalación y ejecución offline en el teléfono propio, identificando versión,
  package y certificado; no una autorización genérica para cualquier build futuro.
- Si se usa ordenador: aprobar depuración USB sólo con un ordenador propio y la recopilación
  local acotada de logs/framestats/archivos de esta beta. No autoriza otros datos ni cuentas.

No se solicitan estas aprobaciones ahora: primero se debe presentar el build, custodia y
expediente concretos. Ninguna se interpreta como concedida por pedir este estudio.

## Protocolo personal reproducible (sólo después de las aprobaciones)

Preparar carpeta privada por hash firmado/commit/run y un teléfono sin root/modificaciones
que debiliten su sandbox. Preferir usuario secundario vacío si HyperOS lo ofrece; no se
asume que esté disponible. No borrar ni exportar sesiones de las aplicaciones existentes.
Si ya hay otra app con ESTE package, detenerse: verificar origen/certificado/datos y decidir
la limpieza explícitamente; no actualizarla ni desinstalarla automáticamente.

Antes de lanzar: modo avión, Wi-Fi/Bluetooth y tethering desactivados; no usar ADB por red.
Estas comprobaciones visuales NO equivalen al aislamiento demostrado de un namespace.
La protección principal continúa siendo el APK sin INTERNET y sus guardas cerradas;
no prometer ausencia universal de IPC/servicios del sistema sólo por modo avión.

Con ordenador propio, registrar únicamente lecturas puntuales (aún no ejecutadas aquí):

```sh
adb -s "$DEVICE" shell getprop ro.build.version.sdk
adb -s "$DEVICE" shell getprop ro.product.cpu.abi
adb -s "$DEVICE" shell getconf PAGE_SIZE
```

No recopilar `getprop` completo, identificadores personales, AccountManager, bugreport ni
Logcat global. No activar root, bajar SELinux o cambiar propiedades globales del linker.
Si la comprobación16KB estricta requiere ajustes no disponibles, dejarla pendiente.
Verificar el hash firmado también después de la transferencia y el package/certificado
instalados antes de abrir. La instalación será manual/autorizada, no realizada por estas herramientas.

| Caso | Acción manual sobre fixtures | Evidencia esperada / cuándo detenerse |
|---|---|---|
| 1 | Abrir desde el icono, primer arranque | UI offline visible; detener si login, permisos sensibles, conexión o crash |
| 2 | Entrar en Settings → Local Python | Resultado JNI/Python listo; «Initialization blocked» es fallo, no PASS |
| 3 | Abrir y cerrar conversación sintética5 veces | Vuelta a lista y estados estables; no mide carga Telegram |
| 4 | Repetir20 ciclos controlados | Registrar fallos/eventos; no afirmar estabilidad sólo por no notar crash |
| 5 | Tocar rápido abrir/Back/abrir | Registrar petición aceptada/cancelada/incompleta, sin convertir tap lógico en latencia táctil física |
| 6 | Back durante transición y gesto disponible | Sin bloqueo persistente; no confundir cancelación de cola con cancelación de animación nativa |
| 7 | Alternar claro/oscuro10 veces | Sin cierre ni vista corrupta; mismas condiciones/escena |
| 8 | Iniciar Python y cambiar tema/volver | Resultado en celda actual; no reaparecen vistas viejas |
| 9 | Home y volver durante navegación | Sin ejecución de petición abandonada; datos de observador incompletos se conservan como tales |
| 10 | Rotar si el sistema lo permite; volver a abrir Activity | Reinicio de sesión de observador identificado; no concatenar dos Activities |
| 11 | Settings → Local observations después de cada bloque | Sólo lotes completos, conservar todos los export_id de la misma sesión |
| 12 | Reabrir tras cierre y revisar logs/métricas | Nuevo PID/sesión; distinguir crash Java, JNI/so, Chaquopy y ANR confirmado |

Ante crash/bloqueo: no repetir indefinidamente. Anotar paso/hash/tema/PID si disponible;
conservar exportaciones completas y reporte saneado. Un timeout de5s del observador NO
es ANR confirmado. El «startup» de PR23 empieza dentro de Activity y no mide todo el
arranque del proceso/Application/JNI anterior.

## Datos privados y herramientas existentes

**No usar `tools/beta_diagnostics/capture.py --execute` en el teléfono personal**:
sigue exigiendo emulador, namespace offline y cuentas vacías. No falsear recibos ni quitar
sus guardas. La vía personal consiste en acciones manuales autorizadas y análisis host
de archivos concretos, con su propio alcance. Sin ordenador puede verificarse arranque/UI
y exportar dentro de la app, pero no prometer métricas recuperadas ni diagnóstico completo
si todavía no hay un medio autorizado para extraer sus archivos privados.

Tras autorización de depuración, la extracción futura puede usar `run-as` del package Debug
para leer SÓLO `files/beta-observer/<sesión>_<exportId>/{observer.json,events.jsonl}`.
No leer preferencias, bases, sesiones, archivos de otras apps o directorios completos.
`run-as` debe funcionar con el build Debug; si HyperOS lo bloquea, no usar root ni relajar
el dispositivo: queda pendiente una vía de exportación app-private revisada por Work2.
Nunca usar `adb backup` para conseguir estos datos. Si el instalador/HyperOS rechaza
el paquete, conservar el error exacto: no desactivar protecciones del sistema ni forzar
instalación para ocultarlo.

Para Logcat: filtrar por PID comprobado de esta app y ventana temporal corta; renovar PID
tras reinicio. Se pueden perder errores de Application anteriores a conocer PID: registrarlo
como limitación, no como «sin crash». Si falta traza, obtener registro individual del fallo
atribuido al package/PID desde el ordenador propio; no exportar logs de otras apps. El
importador nuevo acepta también `--logcat archivo --pids PID` sin `--exports` para
un crash antes de exportar; reutiliza `analyze.logs` sin reescribirlo. Opcionalmente
`--log-window inicio fin` acota época. `--gfxinfo archivo --refresh-hz HZ` reutiliza
`analyze.frames`; si hay varias ventanas requiere revisar `--stream` y el periodo
`--frame-window inicio_ns fin_ns`. Se exige frecuencia observada, no sólo el máximo
publicitado por el panel. No son nuevos collectors ni analizadores. Para framestats usar `dumpsys gfxinfo <package> framestats` sobre esa app,
misma frecuencia/temperatura/escena y ventana; sin datos válidos no hay FPS/latencias.

Nueva utilidad host (sin captura ni ADB) para los lotes de Work2:

```sh
python3.11 tools/personal_beta/import_events.py --source-dir "$PR24/tools/beta_diagnostics" --exports "$SESSION_1" "$SESSION_2" --profile "$PRIVATE_PROFILE" --environment personal_device --apk-sha256 "$SIGNED_APK_SHA256" --output "$NEW_PRIVATE_REPORT"
```

`PRIVATE_PROFILE`: JSON con android_api,abi,page_bytes,compat_mode_disabled (bool o null),
sin serial ni cuenta. Ejemplo ilustrativo, NO medición: `{"android_api":37,"abi":"arm64-v8a","page_bytes":4096,"compat_mode_disabled":null}`.
Sólo aceptar propiedades leídas del dispositivo real para reportes reales.

Importa numéricamente todos los lotes de UNA sesión, incluidos los vacíos. Une antes de
invocar `analyze.interactions` de PR24, porque request/terminal pueden cruzar archivos.
Rechaza `.partial`, huecos, duplicados, mezcla de sesiones, contadores inválidos y contratos
no reconocidos. Pérdidas/abandonos/operaciones incompletas impiden acreditar rendimiento.
Verifica hashes del analizador PR24 mediante PR25; no cambia ningún protocolo histórico.
El informe es0600/exclusivo y se etiqueta `personal_device`, nunca `android_lab`.
No atestigua por sí mismo que el APK indicado se instaló o que el teléfono sea16KB estricto.

## Qué demuestra cada entorno

| Entorno | Comprobable | Pendiente aunque pase |
|---|---|---|
| Host sin Android | Hash/firma/manifest/DEX y ELF estáticos, contratos, empaquetado, analizadores | ART, JNI/Python reales, permisos efectivos, arranque/UI |
| Teléfono personal autorizado | Arranque y fixtures en ESE Android/ABI/página; JNI/Python local y lifecycle | API24 si el teléfono esAPI37; segunda página; aislamiento/tráfico de laboratorio |
| ARM64 API24/4KB aislado | Carga nativa y Python en el mínimo soportado,12 casos y tráfico por UID | API35+/16KB estricto y otros fabricantes |
| ARM64 API35+/16KB estricto aislado | Carga real sin compatibilidad y regresiones en16KB | Fluidez general/producción/autenticación y toda la base de dispositivos |

Ninguna prueba exige exclusivamente emulador: un dispositivo físico dedicado que cumpla
el perfil/aislamiento puede sustituirlo. El teléfono personal actual NO demuestra ambos
perfiles. Si falla firma, aislamiento de identidad/servicios o aceptación ELF/políticas,
no hacer prueba personal hasta resolverlo. Una duda de carga API24/16KB impide certificar
ese perfil; no convierte toda prueba limitada en imposible si el build y el teléfono pasan
las puertas propias y el responsable aprueba explícitamente ese alcance.

## Camino corto y coordinación

Work1 entrega este procedimiento e importador. Work2 conserva su cliente; debe preparar
nuevo build recuperable y expediente concreto, revisar postfirma beta y medio privado.
Responsable aprueba custodia/firma/entrega/instalación/prueba personal limitada. Después,
primer arranque offline, Python, navegación y un reporte acotado del teléfono; corregir el
primer defecto reproducible antes de ampliar pruebas. Los dos perfiles de laboratorio
siguen pendientes para certificar compatibilidad, pero no se presentan como requisito
Android universal para cada prueba personal. No Paso4 ni Production.

Fuentes oficiales consultadas2026-10-20:
- https://developer.android.com/studio/publish/app-signing — firma obligatoria para instalación.
- https://developer.android.com/guide/practices/page-sizes — medir página real y probar carga16KB.
- https://developer.android.com/tools/adb — depuración/dispositivos físicos mediante autorización.
- https://developer.android.com/reference/android/Manifest.permission — INTERNET permite sockets.
