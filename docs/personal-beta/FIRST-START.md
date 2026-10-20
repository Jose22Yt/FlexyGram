# Captura personal de primer arranque — sin cambiar la APK

@Lukhou23 / FlexyGram. Herramienta host independiente, apilada sobre PR26.
No autoriza instalación, firma ni ADB. No cambia cliente/PR23, permisos o contratos.
Código de la APK declarado por el responsable: 97dfb08e58159b31d322dd8435080fb039abdeb9.
PR23 consultado al comenzar: a0e3c23f5f070eaa0fa3c0ecf14f235658d878f4.
La procedencia Git se declara: no puede deducirse del APK por su hash.

## Uso mínimo después de las autorizaciones independientes

1. Conservar APK firmada aprobada, SHA256 y certificado SHA256; conocer versión y
   commit. La herramienta compara SHA256 de los bytes del base.apk instalado con
   ese archivo y verifica su firma v2/certificado con apksigner, sin volver a firmar.
   Lee unos100MB por USB una vez; no guarda una segunda APK. Si Android deniega
   leerla o hay splits, bloquea la captura; no usa root ni alternativas invasivas.
2. Instalación/ejecución offline manual y autorizada, como PR26. Ordenador propio,
   USB previamente autorizado y servidor ADB local ya iniciado por el responsable.
   No prepara servidor, claves ADB, red ni teléfono. Sólo acepta transporte USB;
   si el fabricante no expone el devpath, queda bloqueado, sin degradar controles.
3. Preparar una carpeta NUEVA de informes fuera del repositorio. Recibo privado
   de autorización: schema1, scope=personal_beta_read_only_capture_v1, authorized=true,
   package=io.github.jose22yt.flexygram.beta.development, apk_sha256,
   certificate_sha256, device_serial y approval_reference (mínimo8 caracteres).
   Sólo rellenarlo tras decisión real del propietario para ese APK/dispositivo.
   El JSON registra esa decisión; no autentica por sí solo a quien lo escribió.
4. Revisar primero el plan (no ejecuta ADB):

       python3 tools/personal_beta/first_start.py

5. Con los analizadores PR24 fijados disponibles, ejecutar en el ordenador autorizado:

       python3 tools/personal_beta/first_start.py --execute --authorization "$PRIVATE_AUTHORIZATION" --adb "$ADB" --serial "$USB_DEVICE" --approved-apk "$APPROVED_SIGNED_APK" --apk-sha256 "$SIGNED_SHA256" --certificate-sha256 "$CERTIFICATE_SHA256" --apksigner "$APKSIGNER" --version-code "$BETA_VERSION_CODE" --version-name "$BETA_VERSION_NAME" --commit "$BETA_COMMIT" --source-dir "$PR24/tools/beta_diagnostics" --output-dir "$NEW_PRIVATE_CAPTURE" --observe-seconds 30

   No hay contraseñas ni claves en argumentos. No compartir el recibo con el serial.
   Al aparecer READ_ONLY_WINDOW_READY_MANUAL_ACTIONS_ONLY, abrir/interactuar
   manualmente durante la ventana; la herramienta nunca inicia la Activity.
   Para más detalle de Logcat, iniciar otra ventana con la app YA abierta.
6. Tras usar Settings → Local observations, otra captura puede indicar nombres
   exactos mediante --exports babc_123_1 babc_123_2 (ejemplo ficticio). Sólo lee
   observer.json/events.jsonl de esos lotes con run-as; no enumera archivos,
   preferencias, bases o sesiones. Deben ser TODOS los lotes de UNA Activity,
   desde export_id1. PR26 assemble valida y analiza, sin duplicar su importador.
   Exportaciones inválidas se eliminan del staging privado, sin conservar su texto.
   Si run-as está denegado, queda UNKNOWN; no se modifican permisos del teléfono.

## Qué significa el informe

- Identidad PASS sólo si APK instalada y archivo aprobado coinciden por bytes,
  certificado verificado y versión exacta. Un cambio de ruta/versión durante la
  ventana bloquea el informe. Esto NO sustituye el gate offline/preinstalación.
- JNI/Python/Java/animación: señales de Logcat del PID principal verificado y
  etiquetas concretas, nunca mensajes crudos, rutas privadas o excepciones.
  Otra app/PID, otro usuario Android, PID reutilizado o identidad /proc inaccesible
  no se atribuyen. pm path usa --user current; un cambio de usuario bloquea.
- Exit-info: diferencias entre dos lecturas del package, sin descripciones ni
  trazas. Razones4/5/6/7 confirman cierre OS por crash Java/nativo/ANR/fallo de
  inicialización. EXIT_SELF/USER_REQUESTED/memoria no se convierten en crashes.
  Un cierre normal de la UI tampoco queda demostrado por EXIT_SELF.
- Registro de Activity resumed es sólo evidencia de ese registro; no prueba
  onCreate completo, pantalla correcta o Python/JNI inicializados. Se mantienen
  UNKNOWN hasta prueba visible. Un startup presentado del observador se informa
  por separado; no mide todo Application/JNI anterior ni toque-a-fotón.
- --refresh-hz HZ permite usar el parser gfxinfo ya existente; indicar frecuencia
  observada, no la máxima comercial. --stream selecciona ventana si hay varias.
  El ring buffer NO se resetea ni delimita automáticamente al escenario: informe
  window_scoped=false, sin FPS presentados ni ganador de rendimiento.
- OBSERVED_ERROR_EVIDENCE exige revisión; OBSERVATIONS_ONLY_PENDING_MANUAL_REVIEW
  no significa que Android pasó ni que no hubo crash. BLOCKED sale1; observaciones
  salen0. Sólo report.json (0600), carpeta0700 y lotes validados. Sin subidas.

## Acciones manuales y límites pendientes

PR26 conserva los12 casos. Priorizar primer arranque; Settings → Local Python y
resultado READY; abrir/cerrar conversación sintética; gesto/Back Android17;
toques rápidos/Back durante transición; claro/oscuro; Home/volver y recreación
mediante rotación si está permitida. No cambiar settings desde esta herramienta.
Conservar cada sesión del observador separada y anotar el paso reproducible.

Un proceso que muere antes de conocer su PID no entrega Logcat seguro por esta
vía; exit-info puede confirmarlo después, pero puede estar denegado/demorado.
Un ANR vivo que se recupera puede no aparecer en exit-info; congelamiento manual
no es ANR confirmado. No se lee Logcat global, cuentas, bugreport, tombstones ni
trazas de otras apps para suplir estos vacíos. No se usa el collector de emulador
PR24 ni se relajan sus requisitos. Sin Android real no hay certificación de ART,
JNI/Chaquopy, navegación, HyperOS/Android17,16KB o aceptación de instalación.

## Comprobación de esta implementación

Python3.12.14 disponible; el Python3.11 conservado apunta a un ejecutable ausente.
22 pruebas sintéticas distintas pasan normal y -O, sin dobles conteos. Prueban
los métodos reales con ADB simulado y parsers PR24 verificados por hash; no son
pruebas Android ni ejecución real de apksigner. No se repiten suites históricas.

    PR24_SOURCE_DIR="$PR24/tools/beta_diagnostics" python3 -B -m unittest discover -s tests/personal_beta -p test_first_start.py -v
    PR24_SOURCE_DIR="$PR24/tools/beta_diagnostics" python3 -O -B -m unittest discover -s tests/personal_beta -p test_first_start.py -v

Fuentes primarias de los formatos: developer.android.com/tools/dumpsys y
android.googlesource.com/platform/frameworks/base/+/android17-release/services/core/java/com/android/server/am/AppExitInfoTracker.java;
core/java/android/app/ApplicationExitInfo.java (dump, razones1,4–7).
