# Preparación paralela de laboratorio (sin arranque)

Base revisada: `a5459cf85c2c23e452bb09f38dfe0a28745ecda1`, PR #17.
Esta mejora tiene rama propia y no sustituye el contrato histórico ni el gate
principal que valida el otro Work. No cambia Gradle, políticas Java/JNI,
Production, APK, wheels, ELF ni configuración de servicios.

## Ejecución reproducible

```sh
python3.11 -B -m unittest discover -s tests/lab_readiness -v
python3.11 -B -O -m unittest discover -s tests/lab_readiness -v
python3.11 -B tools/lab_readiness/preflight.py \
  --sdk /ruta/privada/sdk \
  --avd-home /ruta/privada/avds \
  --java-home /ruta/privada/jdk21
```

La salida JSON va a stdout; código 2 significa bloqueo y código 0 solamente
`PREBOOT_CONFIGURATION_CHECKED`. Nunca significa que Android funciona.
El programa no crea directorios, no descarga, no consulta dispositivos y no
inicia el servidor ADB. Únicos subprocesos: `adb version`,
`emulator -no-window -version` y `java -version`, con timeout de 20 segundos.
No ejecuta `adb devices`, `get-state`, `shell`, `install`, `start-server` ni
`emulator -avd`. El código es stdlib y funciona bajo Python 3.11 con `-O`.

Comprobaciones agregadas (continúan después de un fallo):

- Herramientas revisadas: ADB 37.0.1, Emulator 37.2.12 y JDK 21. Una salida
  vacía con exit 0 no acredita una versión. CLI Tools 19.0 y Build Tools
  36.0.0 se contrastan con `source.properties`; esto no certifica sus binarios.
- Raíces SDK/AVD explícitas, sin usar el HOME personal. Espacio conservador
  posterior a materialización: 2 GiB para SDK + 10 GiB para AVD. Si comparten
  volumen, se suma el presupuesto y se comprueba una sola vez. No es una
  estimación suficiente para descargar/extraer imágenes todavía ausentes.
- Los dos AVD revisados deben apuntar a imágenes ARM64 nativas: API24/default
  r9 y API35/google_apis_ps16k r5, incluyendo tag `page_size_16kb` para esta
  última. Se contrastan locator, target, config.ini, ABI, arquitectura,
  rutas, revisión y presencia no vacía de kernel/system/userdata.
- Rechazo de propiedades duplicadas, escapes/symlinks fuera de las raíces,
  particiones de datos externas y Play Store habilitado. Los config.ini de
  ejemplo con rutas temporales deben regenerarse para el hogar privado real.
- Se señalan valores heredados de proxies, selección de dispositivo o servidor
  ADB remoto, precargas LD_PRELOAD/LD_AUDIT y opciones de agentes JVM sin
  publicar sus contenidos. Estas opciones se excluyen de los subprocesos de
  versión, incluso si la inspección sigue para recopilar otros bloqueos. En este host existen proxies;
  no deben borrarse globalmente, sino preparar un entorno offline separado
  autorizado cuando corresponda.

No se vuelven a hashear varios GiB en cada inspección rápida. Es deliberado:
`image_bytes_verified=false` siempre. Antes del arranque deben ejecutarse el
verificador completo existente `lab_host_preflight.py` y las comprobaciones
independientes de procedencia/materialización. Este suplemento NO reemplaza
ese gate, la comprobación de QEMU, la prueba de namespace ni las restricciones
del controlador. No se usa una caché de tamaños/mtime como prueba criptográfica.

## Dos correcciones demostradas del controlador existente

1. `Adb.run`: ADB puede escribir dos avisos estándar de arranque del daemon en
   stderr aunque `get-state` devuelva `device`. Concatenarlos antes hacía fallar
   la comparación exacta del preflight. Se filtran únicamente esas dos líneas
   completas en stderr. stdout, avisos desconocidos, errores similares y exit
   status se conservan. No se introducen reintentos ni nuevas llamadas.
2. `serial_ok`: antes aceptaba puertos 0, 65536 y números arbitrariamente
   grandes. Ahora limita TCP local a 1..65535 y consola emulator a 1..65534
   (el puerto ADB consecutivo también debe caber). No se añaden restricciones
   especulativas de paridad o rango de asignación del emulador.

Las regresiones invocan los métodos reales con subprocess simulado. El registro
previo muestra 8 métodos ejecutados y 6 fallos de aserción (cinco en subtests),
no seis métodos distintos. Después pasan los ocho.

## Qué sigue dependiendo del laboratorio

| Perfil | Precondiciones de preparación | Evidencia todavía obligatoria en Android |
|---|---|---|
| API24, 4 KB | ARM64 nativo, imagen r9, AVD nuevo, almacenamiento privado | API24 real, PAGE_SIZE=4096, arranque, JNI/Python y 12 casos |
| API35+, 16 KB | Imagen revisada API35 r5 con tag 16 KB, sin snapshots | PAGE_SIZE=16384 real, compatibilidad retroactiva desactivada, JNI/Python y 12 casos |

Antes de cualquier arranque autorizado: comprobar QEMU/TCG o aceleración
aplicable a ARM64 (tener /dev/kvm no prueba aceleración ARM64 en host x86),
namespace de red offline real y loopback ADB aislado; plan explícito
`-no-snapshot`; custodia recuperable y revisión de firma; aprobación de
instalación. Este trabajo no arranca dispositivos, no firma ni instala nada.
Las opciones de snapshot de los ejemplos no prueban un fallo si la línea de
arranque las sobreescribe; el plan debe registrar la línea efectiva.

## Diagnostic, laboratorio y futura beta funcional

- `gradle/variant-policy.json`: Diagnostic aislado, seis capacidades cerradas;
  Production buildEnabled=false. `DiagnosticPolicy.java` y política JNI siguen
  intactas. No se deben abrir capacidades para conseguir un PASS del laboratorio.
- `TMessagesProj/src/diagnostic/AndroidManifest.xml`: elimina INTERNET y
  desactiva backup. `TMessagesProj/build.gradle` mantiene identidad y firma
  privada Diagnostic, sin crear una clave automáticamente en esta mejora.
- Harness/instrumentación, fuentes de casos, recibos offline y contratos v1/v2
  son infraestructura del laboratorio, no funciones de una beta. El contrato
  histórico firmado no se repunta a la APK experimental sin firma.
- La fachada de traducción cerrada y las sustituciones nativas experimentales
  no acreditan acceso autorizado a proveedores ni funcionamiento Android.
- Antes de una beta funcional faltan validación real en ambos perfiles,
  revisión de dependencias/ABI y fallos de arranque, custodia/firma recuperable,
  identidad final, API Telegram propia privada y autorización separada de
  autenticación/transporte; revisión de Firebase/push/backup/actualización,
  traducción autorizada, licencias y distribución. Son etapas posteriores;
  esta rama no las implementa ni cambia Production.

## Incorporación sin sobrescribir el trabajo principal

El PR de esta rama apunta a la rama del PR #17 para mostrar únicamente estas
mejoras. No fusionarlo automáticamente. Revisar primero el HEAD actual de #17
con `git fetch`, comparar `run_lab.py` (único archivo existente modificado) y
aplicar los commits mediante cherry-pick/rebase revisado si el Work principal
los acepta. Los demás archivos viven en directorios nuevos.

No se incorpora la suite nueva al gate histórico de 304 pruebas: ejecutar ambos
comandos por separado evita cambiar su contrato y sus conteos. No sumar la
segunda ejecución `-O` como nuevas pruebas distintas. Los logs y el resultado
real de esta sesión se registran en `VALIDATION.md` y `evidence/`.
