# P0.4c — recuperación privada y arquitectura de laboratorio conjunta

Proyecto creado y dirigido por @Lukhou23. Continuación exclusivamente de preparación,
con base en PR17 `ee73f72c44734772fb3f9a67cd0ddd2a4b00f220`.
**No hubo ejecución Android, fusión, APK nueva, firma nueva o promoción de wheels.**
Las 207 pruebas, runner,12 casos, recetas, contratos y evidencias anteriores permanecen
byte a byte intactos. Solo se añaden este informe, probes offline y evidencias de revisión.

## 1. Recuperación comprobada

El mantenimiento retiró el workspace anterior. Se recuperaron desde Git los archivos
publicados, no se reinició el proyecto. Se inspeccionaron archivos de trabajo disponibles,
inventario privado propio/compartido autorizado y metadatos de GitHub. La biblioteca
privada contiene la APK baseline antigua, de tamaño/procedencia diferentes; **no se
materializó ni usó como sustituto**. No hay Releases ni ejecuciones Actions de las que
recuperar artefactos. El endpoint global de artifacts no está expuesto por el conector;
no se declara haber inspeccionado almacenamientos externos no conectados ni cachés remotas.
No se buscaron credenciales de cuentas ni claves ajenas.

| Objeto | Estado actual demostrado | Siguiente acción |
|---|---|---|
| APK experimental125488383 bytes/SHA17c32ab3… | No recuperada | Recuperación privada o reconstrucción controlada |
| 15 wheels originales que integran el overlay | **15/15 recuperados**, SHA256 exacto/CRC válido | Reutilizarlos sin modificación |
| 3 wheels originales FreeType/XML/XSLT usados como insumo | **3/3 recuperados**, SHA256/CRC válidos | Son originales4KB; no son los sustitutos16KB |
| 3 wheels experimentales3flexygram16k | No recuperados | Reconstruir/verificar contra hashes aprobados |
| 4 ELF experimentales | No recuperados | Reconstruir a partir de fuentes fijadas, no extraer del baseline |
| Fuentes XML2.9.8/XSLT1.1.32/XZ5.2.4/binutils2.42 | **4 archivos recuperados**, SHA256 exactos | Usar receta offline existente |
| FreeType | Commit `86bc8a95056c97a810986434a3f268cbe67f2902` recuperado y exportado con git archive | Conservar commit y manifiesto |
| Clave privada laboratorio/certificado27ef63ae… | Clave ausente; certificado/hash documentados | No puede derivarse la clave del certificado |
| Overlay/contratos/96ELF estáticos/207 pruebas | Recuperados de Git, sin cambios | Conservar como evidencias de sus respectivos SHA |

Se descargaron los18 **originales ARM64** desde las URLs ya fijadas en contract.json,
comparando SHA256 y CRC sin instalarlos. No se afirma recuperar los26 wheels del lock
multiarquitectura. La lista individual/origen/hash/bytes está en wheel-recovery.json.

Para evitar otra pérdida de los insumos se guardó una copia **privada** de recuperación,
`FlexyGram-P04c-Recovered-Original-Inputs.zip`,45434269 bytes,
SHA256 `17325285036532db37a4ed09600f5a62a61056de6a2c59bec1d17da550ea0d82`.
Contiene18 wheels originales,4 archivos fuente+export FreeType y manifiestos con hashes.
No contiene APK, wheels experimentales, NDK/JDK, datos de cuenta ni claves. No se publica
el archivo ni su enlace privado en GitHub; aquí solo se versiona su recibo sin identificadores
privados. Esta copia no demuestra recuperación de los tres sustitutos ni del certificado privado.

## 2. Reconstrucción reproducible: posible, todavía no ejecutada aquí

Los insumos fuente/originales son recuperables y la receta existente conserva versiones,
SONAME, exports, grafo GNU y DT_NEEDED, licencias/RECORD y el formato original. No hace
falta diseñar otro compilador o cambiar dependencias activas. Hay evidencia histórica de dos
reconstrucciones iguales; **no se atribuye una reconstrucción nueva a esta continuación**.

Se conserva el procedimiento completo de [EXPERIMENTAL-16K.md](EXPERIMENTAL-16K.md):

1. Recuperar exactamente NDK27.2.12479018, CMake3.31.6, Python3.11/pyelftools0.33 y
   fuentes fijadas. JBR21 fijado ya recuperado. Para APK también SDK37/BuildTools36.0.0,
   Gradle9.7.1/AGP9.3.1, Chaquopy17 y todos los submódulos fijados; no una actualización global.
2. `experiment_recipe.py --build-linker` en destino nuevo; `rebuild_candidates.py` crea
   candidatos LLD; **finalizar** con experiment_recipe.py y GNUld2.42. No aceptar el report
   LLD intermedio ni suprimir la comparación ABI. Mantener LZMA/zlib y la corrección const revisada.
3. Repetir en otro destino nuevo. Comparar los cuatro ELF y tres wheels por bytes/SHA,
   ABI completa/DT_NEEDED y metadatos con evidence-16k-experimental. Si difiere algo,
   detenerse y registrar causa; no actualizar hashes automáticamente ni parchear alineación.
4. Preparar el overlay con prepare_experiment.py solo en worktree desechable del código
   revisado, no modificar build.gradle/locks activos. Reutilizar15 originales recuperados y3
   sustitutos comprobados. Los18 originales ARM64 recuperados cubren select(arm64) de la
   receta; el lock multiarquitectura de26 sigue sin cambios.
5. La APK firmada está bloqueada por falta de clave. No se inició un build sin poder
   satisfacer firma/contrato. Aun recuperando la clave, no se promete SHA idéntico del APK:
   ZIP/timestamps/inputs de build/firma requieren comprobación, no una suposición de determinismo.
   JNI/DEX/recursos/manifiesto y bibliotecas se inspeccionarán por separado ante diferencias.

No se necesitan API ID, API Hash, Firebase, cuentas o servicios para este diagnóstico.

### Procedimiento de nueva clave — únicamente propuesta, NO ejecutada

Primero intentar recuperación del almacén propio mediante su custodio privado. No pedir
contraseñas por chat ni copiar claves a GitHub. Si se confirma irrecuperable, solicitar
aprobación expresa **antes** de generar una clave independiente exclusivamente de laboratorio.
En un host privado autorizado, el procedimiento propuesto es:

```sh
# NO ejecutado en esta etapa. Introducir contraseñas interactivamente/gestor privado.
keytool -genkeypair -storetype PKCS12 \
  -keystore /private/keys/flexygram-diagnostic-lab-v2.p12 \
  -alias flexygram-diagnostic -keyalg RSA -keysize 3072 -validity 3650
keytool -exportcert -keystore /private/keys/flexygram-diagnostic-lab-v2.p12 \
  -alias flexygram-diagnostic -file /private/certificates/lab-v2.der
sha256sum /private/certificates/lab-v2.der
```

Usar un directorio privado nuevo; no sobrescribir nada. Guardar copia cifrada con su
custodio; publicar únicamente la huella del certificado y recibos sin contraseñas.
Configurar la firma Diagnostic por FLEXYGRAM_DIAGNOSTIC_KEYSTORE/STORE_PASSWORD/
KEY_PASSWORD privados; alias actual flexygram-diagnostic. El runner usa sus variables
FLEXYGRAM_LAB_STORE_PASSWORD/KEY_PASSWORD y **el mismo certificado**. Nunca usar esa
clave en Production ni introducir fallback al debug.keystore estándar.

Consecuencias: nueva firma y nuevo SHA APK; no es una actualización compatible de una
instalación con otra firma. La instrumentación con clave nueva **tampoco puede instrumentar
la APK vieja**, aunque se recuperase: Android exige firma compatible. Usar userdata de
emulador totalmente nuevo, sin migrar/restaurar sesiones ni desinstalar apps personales.
Una reconstrucción/revisión separada deberá fijar un nuevo contrato versionado y recibos,
conservar el histórico viejo y verificar el mismo código/políticas. Los hashes antiguos no
se reemplazan silenciosamente y no se promete continuidad de instalación. Ninguna clave
se generó, ninguna APK se firmó o resignó en este trabajo.

## 3. Herramientas e imágenes realmente verificadas

Evidencias en evidence-lab-integration. Al iniciar: host x86_64,4096 bytes, sin herramientas
Android/KVM/TUN/CAP_NET_ADMIN/CAP_SYS_ADMIN. Se recuperaron oficialmente y verificaron
contra checksum del catálogo, calculando SHA256 adicional:

- platform-tools37.0.1: `adb version` exit0. No se inició adb server ni se conectó a un dispositivo.
- Emulator37.2.12 build16428233: `-no-window -version` exit0; incluye qemu-system-aarch64
  headless para host Linux x86_64, cuya opción **-version** también pasó. Esto demuestra que
  el motor está disponible, **no** que una imagen Android haya arrancado. La opción inicial
  --version del motor no está soportada; se corrigió a -version, sin intentar boots.
- Launcher gráfico `-version` falló por libxkbfile.so.1 ausente; headless evita esa ruta.
- `-accel-check` exit3: KVM no disponible/VMX-SVM no expuesto. No se cambió el host.

**Se corrige la hipótesis demasiado amplia de que falta un motor ARM64:** el paquete
actual sí lo incluye. Su ejecutable es ELF x86_64 porque corre en el host; el guest que
validaría las bibliotecas debe seguir siendo ARM64 nativo, comprobado con uname/ABI y
sin native bridge. Un Android x86 con ARM traducido no sirve.

Catálogos oficiales consultados de nuevo, más HEAD HTTP de los archivos de imágenes:

| Laboratorio | Imagen oficial | Estado actual |
|---|---|---|
| A:API24/ARM64/4096 | android-24;default;arm64-v8a,r09 | Catálogo y URL disponibles; no descargada/instalada/arrancada |
| B:ARM64/16384 | android-35;google_apis_ps16k;arm64-v8a,r05 | Catálogo y URL disponibles; falta comprobar página real |
| B alternativa | android-36;google_apis_ps16k;arm64-v8a,r07 | Catálogo y URL disponibles; no ejecutada |

No se descargaron imágenes de varios GB ni se repitieron intentos de arranque sin
artefactos/firma y aislamiento verificable. **No hay laboratorio A o B funcional demostrado.**
La inspección de disponibilidad no certifica PAGE_SIZE ni compatibilidad API24.

### Viabilidad por software y elección de host

KVM ausente no descarta TCG. El motor ARM64 SDK actual responde headless y Cuttlefish
contempla QEMU/TCG; ambas rutas necesitan un boot controlado y medido para cualificarse.
La rama de Emulator emu-35-3 examinada anteriormente contiene restricciones de ARM64
sobre x86: no extrapolarlas sin prueba al binario37.2.12. Sus binarios incluidos tampoco
prueban por sí solos que el launcher soporte todas las imágenes/API en TCG. SwiftShader
es emulación gráfica, no prueba de CPU ARM64.

Ruta preferida: host de laboratorio dedicado/autorizado capaz de ARM64 nativo o TCG
compatible, con control de red, espacio para imágenes y userdata desechable. Para A usar
la imagen AOSP24 y motor fijado que la arranque; para B imagen ps16k ARM64 o Cuttlefish
con kernel16KB. Mac ARM64 puede ser candidato con SDK darwin_aarch64, pero requiere
verificar soporte de ambas imágenes y un control UID/root compatible: no se da por validado.
Linux ARM64/Cuttlefish exige tooling propio compatible, no instalar binarios linux_x64 a ciegas.

Procedimiento operativo existente en [ANDROID-INSTRUMENTATION.md](ANDROID-INSTRUMENTATION.md):
namespace/red exterior bloqueada y ADB local, recibo de procedencia imagen/motor/kernel,
AVD nuevo sin snapshots/cuentas, root únicamente laboratorio, comprobar uname/ABI/API/
PAGE_SIZE y modo16KB estricto. Si TCG funciona sin KVM, probar una vez con límite
explícito de boot y logs; si falla, conservar la causa y detener esa ruta, no cambiar a guest x86.
El runner debe seguir rechazando entornos sin estas pruebas. La ausencia de permisos de
namespace aquí impide aplicar el aislamiento Linux propuesto; una alternativa de red totalmente
suprimida en QEMU sería posible, pero su configuración y comprobación aún están pendientes.
No declarar imposibilidad universal por falta de KVM/TUN, ni arrancar con una red sin verificar.

## 4. Comparación comprobada de PR17,20 y21

HEAD revisados, todos borrador/abiertos hacia develop:

- PR17 `ee73f72c44734772fb3f9a67cd0ddd2a4b00f220`.
- PR20 `9efbcbb710a31280b2c20e7d1733ff21ec083cb4`.
- PR21 `88f988ee844248a4513281cfe7818777fbda660e`.

| Control | PR17 existente | PR20 | PR21 |
|---|---|---|---|
| API/página/ARM64 | Preflight host y proceso objetivo, uname/ABI primaria/bridge/16KB estricto | API/página real, **solo pertenencia ARM64 en abilist**, QEMU | Campos JSON autodeclarados; tipos numéricos estrictos |
| APK/firma/permisos | Hash/tamaño+wheels/ELF; certificado en app; manifiesto de runner; permisos instalados | aapt2 manifiesto local y apksigner **v2 explícita**, hash/cert configurables | Compara pins constantes declarados, sin abrir APK |
| Entorno limpio/aislamiento | Cuentas vacías, otros clientes, root, recibo host, UID DROP IPv4/IPv6 | Rechaza Diagnostic preinstalado; consultas readonly, sin aislamiento exterior | Solo declara counters0, sin corroboración independiente |
| Arranque/JNI/Python | Único productor: Activity,JNI marker,Chaquopy test-only y12 casos reales preparados | No ejecuta | No ejecuta; comprueba pass declarado |
| Cuatro ELF | Hash de wheel/APK y mappings antes/después | No inspecciona | Cuatro hashes autodeclarados |
| Logs | Captura privada/logs críticos/hash de evidencia | **Conteos sin líneas**, categorías Python/OOM adicionales | Requiere contadores0, no analiza logs |
| Casos omitidos |12 IDs exactos/counts/skips/errores/nonces/matriz | No cubre |12 IDs exactos/estados, rechaza desconocidos |
| JSON/privacidad | Historial/logs completos solo de entorno limpio; no es atestación criptográfica | Report resumen sin serial crudo; no stderr de comandos | Rechaza claves duplicadas/no finitos/fields extra/bool numérico/symlink/tamaño |

Los hashes APK/cert/4ELF y12 IDs de PR21 coinciden **exactamente** con contract.json.
No hay conflictos de valores actuales; sí hay contratos de datos incompatibles:

| Concepto | PR17 | PR20 | PR21 |
|---|---|---|---|
| Perfiles | api24-4k / arm64-16k | api24 /16k | profiles.api24 /profiles.16k |
| Página/API | environment.page_size /api | target.page_size_bytes /android_api | page_size_bytes /api |
| Certificado | certificate_sha256 | apk.lab_certificate_sha256 | cert_sha256 |
| Tests/librerías | Arrays con IDs/hash/mapping y counts | No presentes | Diccionarios ID→pass y nombre→hash |
| Éxito | PASS por run; PASS_BOTH_ANDROID_LABS de matriz | READY_FOR_HUMAN_REVIEW… o **partial exit0** sin APK | CONSISTENT_SELF_REPORTED_EVIDENCE_REQUIRES_HUMAN_REVIEW; runtime_certified=false |
| Localidad | emulator-N y localhost Cuttlefish comprobados | Solo emulator-N/QEMU | No observa dispositivos |

No conectar herramientas solamente por exit0 ni convertir PASS mediante renombrado
ciego. PR21 rechaza la salida directa PR17; se reprodujo con fixtures. Exportar un resumen
hacia PR21 perdería nonce,fuentes,18wheels,scope,paths,strict16KB y hashes de logs si se
usase como evidencia primaria. El informe primario PR17 debe conservarse siempre.

### Hallazgos reales y pruebas adicionales de revisión

`evidence-lab-integration/contract_probes.py` reproduce sin Android:

1. PR20 **acepta** `x86_64,arm64-v8a` en abilist y no consulta uname, ABI primaria ni native
   bridge. No prueba un bypass de PR17: el guard de PR17 rechaza el entorno sintético
   traducido. **Corregir PR20 antes de usarlo como preflight autoritativo**, conservando
   solo lectura y los controles más fuertes de PR17. No modificar los motores Android.
2. Con log sintético FATAL EXCEPTION+ModuleNotFoundError, PR20 devuelve exit0/READY y
   conteos>0. Es coherente con su límite de preflight, pero **no puede servir de gate final**.
   El orquestador debe bloquear por cualquiera de esos indicadores; ausencia de log/categorías
   requeridas es bloqueo, no cero implícito. Registrar limitaciones/falsos positivos.
3. PR21 rechaza un resumen PR17 directo y mantiene runtime_certified=false incluso con
   fixture todo-pass. Su CLI no acredita ejecución, identidad del kernel o modo16KB estricto.

Son fixtures/mocks, no fallos observados en un teléfono. No se modificaron los PR20/21:
se prepara la corrección y adaptación para aprobación. Sus READMEs deben reconocer que
el productor ya existe en PR17, en lugar de proponer otro androidTest desde cero.

## 5. Arquitectura única recomendada y validación conjunta

**Conservar PR17 como único productor y controlador de instalación/arranque.** Reutilizar
PR20 como fase readonly de inspección local y clasificador privado de logs; PR21 como
verificador secundario de coherencia de un resumen. No duplicar runners,estados Android,
12casos o archivos de pins. Este trabajo no implementa una integración parcial que dé éxito
sin disponer de todas las herramientas; documenta una adaptación versionada pendiente.

Orden de ejecución propuesto, con bloqueo explícito en cada fase:

1. Contrato único versionado y aprobado en PR17: SHA código/runner/APK,cert,18wheels,
   4ELF,JNI,12casos,fuente/font/licencia. Importar los pins a los adaptadores; evitar tres copias
   que diverjan. PR20 no puede aceptar huellas arbitrarias proporcionadas por el operador
   como sustituto del contrato aprobado. No alterar las denegaciones ni añadir credenciales.
2. Preflight readonly reutiliza apk_probe/v2/manifiesto y counters sin líneas de PR20,
   pero añade las verificaciones fuertes de PR17: uname aarch64,ABI primaria,bridge vacío,
   perfil estricto,imagen/motor/hostoffline,cero cuentas/paquetes existentes. Mapeo explícito
   de perfiles. Admitir Cuttlefish local solo mediante la misma identidad comprobada del runner.
   Partial exit0 de PR20 **bloquea** una ejecución conjunta que requiere APK verificada.
3. Solo el run_lab existente instala APKs exactos y firmados de igual certificado en
   emulador nuevo; bloquea UID antes de arranque. Activity,cold-launch,JNI guard y
   Chaquopy test-only,4paths/ELF antes/después y los12 casos fuente intactos, en A y B.
4. Recoger logs/contadores reales y sus hashes. Reutilizar categorías PR20 y ampliar
   cobertura donde corresponda, con cero errores críticos para aceptación. No copiar datos
   de cuenta, Throwable sensibles o credenciales. Los contadores de log no son conteos de
   incidentes únicos; para aceptar cero no importa deduplicación, para diagnosticar sí.
5. Matrix PR17 exige ambos perfiles,nonces distintos,12/12 por perfil,logs presentes y
   hashes coherentes. La adaptación debe reanalizar counters/logs desde archivos, ligar
   imagen/commit/runner a cada run y mantener guardas de tipos/claves duplicadas de PR21;
   no confiar solo en un campo status ni en valores rellenados manualmente.
6. Solo después de esa matriz y análisis, generar **resumen derivado** de esquema PR21,
   con mapeos explícitos y referencia hash al conjunto primario. Ningún pass o contador0
   por defecto: si falta evidencia, rechazar. PR21 valida resumen estrictamente y conserva
   runtime_certified=false; no sustituye el origen primario ni autoriza beta/fusión.
7. Revisión humana de fuentes,ABI/API/página real,firma,mappings/logs y límites de red.
   Cero paquetes UID durante intervalo no prueba ausencia universal de IPC delegado o
   actividad fuera del intervalo. No confundir revisión de JSON con atestación independiente.

Pruebas de la futura adaptación: formatos incompatibles,campos/claves duplicados,
bool/int,fuente ausente/huella divergente,skip/fail/error/xfail,case duplicado,archivo de
counter/log modificado,fallo Python/OOM sin FATAL,nonce repetido,APK/runnercert distinto,
ABI traducida,permisos,16KBcompat habilitado y entorno sin APK. Positivos exclusivamente
sintéticos hasta disponer de laboratorios; nunca mezclarlos con recibos Android reales.

## 6. Auxiliares, conflictos y orden de integración recomendado

No se fusionó ningún PR. Todos conservan HEAD revisados. Se ejecutó merge-tree de solo
lectura, base explícita develop `ab063041804674861e865364206c0ef27ef1e953`, contra
PR17 aprobado. **Cero conflictos textuales por pareja**. No equivale a ejecutar todos los
PR combinados ni garantiza coherencia de contratos/guardas. Árboles/paths/hashes exactos
en aux-integration.json. Las30 rutas auxiliares quedan fuera del alcance congelado actual.

| PR/HEAD | Verificación nueva | Recomendación/orden |
|---|---|---|
|20/9efbcbb710a31280b2c20e7d1733ff21ec083cb4 |22/22 normal y-O; dos límites reproducidos | **1º**, tras corregir ABI/bridge,documentación y semántica de gate readonly |
|21/88f988ee844248a4513281cfe7818777fbda660e |24/24 normal y-O; pins/12IDs idénticos | **2º**, con adaptación explícita y pruebas de contrato, sin reemplazar runner |
|16/fe3b8973b44a74fcbba3aedc92a514f3b1462e80 |8/8; auditor strict exit0,0errores/10review | **3º**, auditor auxiliar reutilizable; sin renombrar app ni corregir créditos a ciegas |
|19/103e9e6b1fada37254ce788d0cb2c19e65891c36 |15/15; strict exit0,11/11 señales | **4º**, contenido favorable,solo auditoría; no inferir FPS/latencia ni tocar rendimiento |
|18/44f9826e2d5d74634a85374962da07b068f39efa |6/6 recursos; no nuevo AAPT2/buildAndroid en este turno | **Último**, tras estabilizar evidencia P0.4c y revisión de marca; icono NO activar |

Orden de prioridad para revisión futura, **no autorización de merge ahora**. PR16/19
podrían revisarse en paralelo sin bloquear los primeros boots; no son requisitos para
cargar JNI/Python. PR18 cambia8 strings y añade recursos candidatos: requiere revisión
funcional/recursos y delimitación por archivos/hash, aunque no haya conflicto textual.

Antes de cualquier integración aprobada: revisar los30 archivos exactos y sus antes/después,
añadir excepciones **por ruta y huella revisada** en el contrato adecuado, no permitir
prefijos globales tools/,tests/ o todos los recursos; ejecutar207 regresiones conservadas
más suites auxiliares y adaptación sobre la combinación real. Un archivo no revisado
sigue bloqueando. No cambiamos allowlists ni regeneramos huellas en esta continuación.

## 7. Resultados ejecutados y qué NO se ejecutó

Nuevos logs de Python3.11.17:32 del runner+22 PR20+24 PR21+8 PR16+6 PR18+15 PR19
= **107 pruebas únicas aprobadas**,0 fallos/omisiones. Las primeras78 también se
repitieron con -O, sin contarlas dos veces. Probes de comparación adicionales offline
aprobados en normal/-O. PR16/19 strict exit0; hay11 señales de navegación y10review de identidad.

Las207 anteriores se **preservan como suite y evidencia histórica intacta**; no se
anuncia una nueva ejecución completa de207 aquí (solo32 del runner se reejecutaron).
No hubo nuevo build del cliente, de ELF/wheels reconstruidos o del test APK; su build
previo unsigned sigue documentado. Sin ejecución de los12 casos sobre Android,
instalación,medición PAGE_SIZE de guest,restauración sintética,JNI/Python reales o tráfico
UID. El inventario4096 de esta máquina es del **host**, no de Android.

## 8. Bloqueos y recursos/autorización concretos

- APK experimental,3 wheels reconstruidos,4 ELF y clave exacta no recuperados.15/18
  wheels del overlay sí recuperados. La ruta de insumos para reconstrucción está preparada,
  pero faltan las herramientas nativas/Gradle/SDK completas y comprobación de reproducibilidad nueva.
- Si el custodio dispone de APK/overlay/keystore originales, debe aportarlos **por canal
  privado autorizado**, nunca valores de claves/contraseñas públicamente. No hacen falta
  cuentas Telegram ni un teléfono personal. No hay que volver a aportar los18 originales ya guardados.
- Si la clave es irrecuperable, falta aprobación explícita para crear clave **solo laboratorio**,
  reconstruir con ella y revisar un nuevo contrato/firma/hashes. Esta aprobación no está
  implícita en la preparación actual y no se ha pedido al usuario ejecutar comandos todavía.
- Host aislable compatible ARM64/TCG,imágenes instaladas y cualificadas para ambos
  perfiles,controles root/UID y modo16KB estricto. ADB/Emulatorheadless ya comprobados
  son avance de preparación; no sustituyen esos recursos. No se necesitan laboratorios
  externos ni subirles APK: requerirían autorización independiente y no se proponen como acción actual.
- Aprobar correcciones/adaptación de PR20/21 y posteriores merges individualmente;
  PR17 queda borrador hasta revisar evidencia y aprobarlo. No se implementó otro runner.

Main sigue `db1bea24b7b705de33f8ff8c8e174011c153cac7`,protegida; develop intacta;
PR2 abierto. Sin Actions habilitado,Production,autenticación,servicios externos,icono
activado,APK distribuida,cambio de interfaz/animaciones/rendimiento o Paso4.

## Fuentes primarias y comandos

- https://dl.google.com/android/repository/repository2-3.xml
- https://dl.google.com/android/repository/sys-img/android/sys-img2-3.xml
- https://dl.google.com/android/repository/sys-img/google_apis/sys-img2-3.xml
- https://developer.android.com/guide/practices/page-sizes
- https://developer.android.com/studio/run/emulator-acceleration
- https://source.android.com/docs/core/architecture/16kb-page-size/getting-started-cf-arm64-pgagnostic
- Cuttlefish TCG: https://android.googlesource.com/device/google/cuttlefish/+/8b75d1f30a7611e5fbcd03146889d7e20a174120/host/libs/vm_manager/qemu_manager.cpp

Probes reproducibles, usando los tres HEAD exactos en directorios separados:

```sh
python3.11 docs/security-p04c/evidence-lab-integration/contract_probes.py \
  --pr17-root /private/checkouts/pr17 \
  --pr20-root /private/checkouts/pr20 --pr21-root /private/checkouts/pr21
python3.11 -m unittest discover -s tests/android_lab_preflight -v # en PR20
python3.11 -m unittest discover -s tests/android_lab_evidence -v  # en PR21
```

Los archivos de evidence-lab-integration incluyen los resultados,inputs públicos,
HEAD/huellas por archivo y hashes de evidencias; nunca binarios,claves o datos personales.

Dos logs de versión publicados normalizan únicamente líneas vacías finales; log-normalization.json conserva hashes raw y publicados.
