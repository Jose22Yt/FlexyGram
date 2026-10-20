# P0.4c — APK experimental ARM64 reconstruida sin firma

Ejecución real del 20 de octubre de 2026 (UTC). FlexyGram, creado y dirigido por @Lukhou23.
PR #17 permanece en borrador, sin fusionar. No certifica Android ni autoriza distribución.

## Resultado principal y trazabilidad

**APK generada y conservada privadamente**, desde el código exacto
`1177ceb8f4351b1626dd65e3dbd657f3b0ff159f`. Se preservaron los tres commits
`33374860`, `3e3c209a` y `1177ceb8`. El commit que publica este informe añade
solo documentación/evidencias: no es un nuevo código Android compilado.

| Comprobación | Resultado real |
|---|---|
| Gradle | `:TMessagesProj:assembleDiagnosticDebug`, **BUILD SUCCESSFUL**, 11m34s, exit 0 |
| Tareas del intento final | 248: 41 ejecutadas, 207 actualizadas; se reutilizó el trabajo de los intentos de esta sesión |
| Nativo | JNI y runtime Chaquopy compilados realmente, `NATIVE_TARGET=arm64-v8a`, sin SKIP nativo |
| Fuente | Worktree independiente de `1177ceb8`, overlay experimental de wheels y retirada de asignación de firma |
| APK | `flexygram-v13.0.2(1261)-diagnostic-debug-unsigned.apk`, **113080183 bytes** |
| SHA-256 | `291881863ea81418fa6cb12104b6eaea4aee2403822894da2143a51f3030bdd5` |
| Firma | Ausente: sin entradas JAR de firma ni bloque APK; apksigner rechaza por falta de firma |
| Integridad/empaquetado | CRC válido y `zipalign -c -P 16 -v 4` aprobado |
| Android | **No instalado ni ejecutado**; APK unsigned no instalable |

Registro: [recibo APK](evidence-unsigned-rebuild-20261020/unsigned-apk-receipt.json),
[build](evidence-unsigned-rebuild-20261020/build-result.json),
[log completo depurado](evidence-unsigned-rebuild-20261020/gradle-unsigned.log).
Solo se ocultan las opciones locales de proxy/TLS en las líneas `JAVA_TOOL_OPTIONS`;
no se ocultan errores ni se suprimen advertencias del compilador.

## Recuperación y pruebas

- Recuperados los dos respaldos privados originales. El de reconstrucciones tiene
  SHA-256 `979c5c5f61519949dd677a6d4892fbd13e202af803b291b0b7003b4c5bd2ecb2`;
  el de inputs originales, `17325285036532db37a4ed09600f5a62a61056de6a2c59bec1d17da550ea0d82`.
- Verificados sus 44 miembros fijados, 18 wheels originales y el overlay cerrado
  de 18 wheels experimentales (3 reconstruidos, 15 originales). Los cuatro ELF y
  tres wheels conservan exactamente los hashes aprobados. No se reconstruyeron otra vez.
- Comparación ABI de los cuatro ELF frente a sus originales aprobada. Las filas A/B
  recuperadas coinciden: esta es verificación de evidencia histórica, **no una nueva ejecución A/B**.
- **231/231 pruebas** Python **3.11.17**, normal y `-O`, 0 errores/fallos/omitidas.
  El gate host de preparación pasó 54/54 en ambos modos; sus casos son un subconjunto,
  no se suman como nuevas pruebas únicas.
- El primer gate falló porque el clon superficial no tenía el commit base del control
  de alcance. Se recuperó el historial y se repitió íntegro sin editar pruebas.
- Dos intentos iniciales de Gradle fallaron por preparación local: metadatos SDK
  inválidos y CMake no localizado por el script Chaquopy. Se corrigieron el namespace/licencia
  del SDK, los 35 enlaces oficiales del NDK y las rutas CMake/Python/Ninja. No se parcheó
  el cliente. Los logs y resultados fallidos se conservan separados del éxito final.

[Pruebas normal](evidence-unsigned-rebuild-20261020/native-231.json) ·
[Pruebas -O](evidence-unsigned-rebuild-20261020/native-231-opt.json) ·
[Recuperación](evidence-unsigned-rebuild-20261020/recovery-verification.json) ·
[ABI](evidence-unsigned-rebuild-20261020/recovered-abi.json) ·
[Toolchain](evidence-unsigned-rebuild-20261020/toolchain-receipt.json).

## Auditoría de los bytes nuevos

- Paquete `io.github.jose22yt.flexygram.diagnostic`, versión `13.0.2 (1261)`,
  ABI instalable solo ARM64; minSdk24, compileSdk37 y targetSdk36 conservados.
- **97 ELF inspeccionados, 96 AArch64**: 96/96 cumplen PT_LOAD de 4 KB y 16 KB;
  cero bloqueadores estáticos API24 por DT_NEEDED, símbolos fuertes o versiones.
  El auxiliar x86-64 de debugpy permanece visible como payload no objetivo.
  Los avisos RELRO se evalúan por solapamientos reales; no se convierten automáticamente en fallos.
- Los cuatro ELF experimentales empaquetados coinciden byte a byte con los aprobados.
- 1833 comandos JNI (1832 archivos fuente únicos), todos para `aarch64-none-linux-android24`.
  Las tres guardas de inicialización/transporte/socket revisadas contienen solo `RET`;
  la sección `.text` empaquetada coincide con la biblioteca enlazada sin stripping.
- BuildConfig y JNI concuerdan: API ID0, API Hash vacío, seis capacidades falsas,
  identidades de datos/proveedores propias. Sin `INTERNET`.
- Se conservan únicamente `ACCESS_NETWORK_STATE` y el permiso privado de receptor.
  Solo el alias launcher revisado está habilitado y exportado. La superficie fusionada
  y sus mutaciones negativas pasan el verificador existente.
- 73595 clases DEX, ninguna duplicada; seis clases de fachada Diagnostic presentes una vez,
  sin dobles de laboratorio ni clases extra del AAR de traducción retirado.
- Escaneo de APK, JAR de fachada y **201 artefactos externos** aprobado para los patrones
  e identidades retiradas registrados. Esto **no es una afirmación universal de ausencia
  de cualquier secreto**, ni una prueba de tráfico real. Los cuatro grafos Debug/Staging
  conservan los mismos identificadores de componentes que los históricos.

[ELF completo](evidence-unsigned-rebuild-20261020/apk-native-audit.json) ·
[Aceptación estática](evidence-unsigned-rebuild-20261020/apk-native-acceptance.json) ·
[Manifest/Java/JNI/escáner](evidence-unsigned-rebuild-20261020/apk-diagnostic-check.json) ·
[Guardas enlazadas](evidence-unsigned-rebuild-20261020/native-linked-guards.json).

## Diferencia frente a la APK histórica

El histórico unsigned `ddb7b017838a2a13991ac09154bbf252a11d62326e9a588349ca03c115e01699`
no se recuperó. El candidato nuevo mide 600 bytes menos y tiene otro SHA-256.
**No se ha sustituido ningún hash ni contrato histórico**, ni se ha presentado el
verificador privado ligado al hash anterior como prueba de este candidato diferente.

Se cotejaron los 97 hashes ELF históricos: **96 iguales**, incluido Chaquopy y los cuatro
reconstruidos; solo difiere `libtmessages.49.so`. Los grafos de dependencias son iguales y
`git diff` no encuentra cambios Android/Gradle/JNI/módulos desde el código compilado
histórico `723580b5` hasta `1177ceb8`.

La biblioteca nueva contiene 447 cadenas con rutas del entorno de compilación actual;
los logs históricos muestran otra raíz de worktree y WebRTC utiliza `__FILE__`.
Las rutas y el layout del enlace pueden cambiar el binario: es una explicación técnica
compatible con lo observado, **no una atribución exhaustiva de la diferencia**.
Sin los bytes antiguos no puede compararse cada sección/entrada de ambas APK ni
certificarse reproducibilidad bit a bit del conjunto. No se modificaron flags o pins para
forzar una coincidencia. El nuevo candidato queda sujeto a revisión independiente.

[Comparación](evidence-unsigned-rebuild-20261020/historical-comparison.json) ·
[Rutas nativas observadas](evidence-unsigned-rebuild-20261020/native-build-path-observation.json).

## Conservación privada verificada

Respaldo **`FlexyGram-P04c-Unsigned-Candidate-1177ceb8-Private.zip`**,
302608432 bytes, SHA-256
`c1c5caea6b949ea97ce4e912e17639c7d372aeb6def42a5c17909ebdfa963812`.
Incluye APK unsigned, respaldo nativo con fuentes/18 wheels, JNI enlazado sin stripping,
comandos de compilación, runtime Chaquopy, manifiesto, BuildConfig, recetas usadas y logs.

Se recuperó desde almacenamiento privado en un segundo directorio y se verificaron
SHA-256 del ZIP, CRC y **58/58 hashes/longitudes de miembros**, incluida la APK exacta.
No contiene una clave privada de firma. No se publican ni enlazan binarios en este PR.
[Recibo de conservación](evidence-unsigned-rebuild-20261020/private-preservation.json).

## Android: bloqueo específico y siguiente puerta

Host x86-64, páginas del **host** de 4096 bytes, sin `/dev/kvm` ni `/dev/net/tun`.
La creación de un namespace de usuario/red falla con `Operation not permitted`.
Se recuperó emulator37.2.12 y se ejecutaron correctamente las consultas de versión
headless y del motor ARM64. La consulta GUI requiere libxkbfile, pero ese error no
bloquea por sí mismo la consulta headless. `-accel-check` devuelve3: KVM no disponible.

Las URLs oficiales API24 ARM64/4KB y API35 ARM64/ps16k responden HTTP200 con longitudes
esperadas. **No se descargaron ni arrancaron imágenes en esta sesión**. La presencia
del motor y la opción de desactivar aceleración no prueban viabilidad de TCG ni
arranque offline; la ausencia de KVM tampoco demuestra que TCG sea imposible.
No se sustituyó ARM64 por x86-64 ni se supuso el tamaño de página de un invitado inexistente.

Queda pendiente, antes de firmar o probar:

1. Revisar este candidato nuevo y el procedimiento/contrato versionado para su futura firma.
   No generar claves sin custodia privada recuperable verificada y autorización aplicable;
   la autorización actual no permite generar, firmar, instalar o distribuir.
2. Disponer de un laboratorio ARM64 offline con aislamiento de red comprobado y herramientas
   funcionales. Mantener los perfiles API24/4KB y API35/16KB estricto existentes.
3. Tras autorización independiente, instalar APK y runner con identidad de laboratorio
   aprobada y ejecutar **12/12 casos en ambos perfiles**, primer arranque, JNI/Python,
   XML/XSLT/EXSLT/lxml/Pillow, permisos/componentes, restauración sintética, errores y
   contadores de tráfico. Registrar API/ABI/página real, firma, hashes, nonce y logs;
   rechazar omisiones o entorno incorrecto mediante el runner existente.

[Probes actuales](evidence-unsigned-rebuild-20261020/lab-probe.json) ·
[Disponibilidad de imágenes](evidence-unsigned-rebuild-20261020/image-availability.json) ·
[Runner conservado](ANDROID-INSTRUMENTATION.md).

No se modifican main, develop, Production, autenticación, permisos activos, interfaz,
animaciones, dependencias activas ni contratos históricos. No se fusiona PR, no se
habilita Actions, no se generaron claves ni se firmó, instaló o distribuyó la APK,
y no se inicia el Paso4. La compilación y los controles estáticos están verificados;
**instalación, arranque y compatibilidad Android real siguen pendientes**.
