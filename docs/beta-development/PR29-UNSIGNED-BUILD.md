# Segunda beta offline: PR29 integrado y APK unsigned compilada

FlexyGram1.0, creado y dirigido por @Lukhou23. PR23 continúa en borrador.
No es una beta operativa ni una autorización de firma, entrega o instalación.

## Código y regresiones ejecutadas

PR29 revisado en `be75bdb65ddb5ae5a68024a985295eae7f612dd8`, sobre PR23
`78151d9e8083290dca2617279cab3afb53540de6`. Sus ocho archivos se incorporan exactos:

- `ef1ce2d22506f4258b48f11c3e644ef5000214ce`: equivalente revisado de `2308d37e…`.
  Puente Back API33+ con registro/cierre idempotentes, callbacks tardíos invalidados,
  delegación a la cola existente y cuerpo legacy API24–32 conservado.
- `97dfb08e58159b31d322dd8435080fb039abdeb9`: equivalente revisado de `be75bdb…`.
  Inicialización beta por proceso NEW/RUNNING/READY/FAILED; tras fallo no construye UI
  parcial al recrear Activity ni vuelve a ejecutar el inicializador. No resetea el flag
  heredado, no guarda excepciones ni registra valores sensibles.

Los originales y su documentación «no ejecutada por Work1» conservan su procedencia.
Esta ejecución sí comprobó las8 regresiones nuevas normal/-O, con controles originales
que fallan y versiones corregidas que pasan. Suite completa: **68 métodos distintos
PASS en ambos modos, cero omisiones**:36 cliente,11 importador,21 handoff. Los8 están
incluidos en68; no contar sus ejecuciones separadas ni los dos modos como métodos nuevos.

Son pruebas host CPython3.11.17/JDK21 con dobles Android explícitos; no ART ni dispatcher
real en dispositivos. Los casos simulan API24/32/33/36/37. Java nuevo también compiló
contra SDK37 real. No certifica funcionamiento en Android17.

## Recuperación y corrección del entorno

El mantenimiento dejó el workspace y /root/.gradle/caches vacíos. No se atribuye su
eliminación al usuario ni se afirma continuar un proceso/caché que ya no existía.
Se recuperaron el repositorio, los16 submódulos fijados y el respaldo privado Diagnostic
con SHA256`c1c5caea6b949ea97ce4e912e17639c7d372aeb6def42a5c17909ebdfa963812`.
De él se recuperó el archivo nativo61MB con hash histórico exacto. Verificados18 wheels
originales y18 overlay; **no se reconstruyeron los4 ELF ni los3 wheels experimentales**.
No se recuperó la APK beta histórica98de3527… ni se cambió su hash.

También se recuperaron herramientas fijadas JDK21.0.10, Gradle9.7.1, SDK35/37.0,
BuildTools36, NDK27.2.12479018, CMake3.31.6, Ninja1.12.1/Python3.11.17. Descargas nuevas,
no caché histórica. Las copias de submódulos del checkout de build reutilizan objetos
locales, sin descargarlos dos veces. Se conserva el proxy/TLS; propiedades de proxy
se pasan directamente a Gradle. No se repite el problema Library403 ni se elude.

Primer intento: fallo antes de compilar la app, plataforma37.0 recuperada sin registro
SDK utilizable. Se corrigió únicamente la instalación local: directorio canónico
platforms/android-37.0 y package.xml derivado del paquete exacto del catálogo oficial,
revisión2/checksum ZIP coincidente. android.jar conserva SHA256
`bf1b4387cc7ca94fc6ef684f040d9d16fbf16248e181819f020736ea2053f177`.
No se cambia SDK, target/minSdk, archivo JAR ni configuración activa del proyecto;
no se vuelve a descargar la plataforma. [Registro](evidence-pr29-build/sdk37-registration.json).

## Compilación real y APK

**Código realmente compilado:** `97dfb08e58159b31d322dd8435080fb039abdeb9`.
Commits documentales posteriores no son recompilaciones. Checkout hermano aislado,
receta unsigned y copia nueva del manifiesto/lock experimental; locks activos intactos.
BUILD_COMMIT_ID conserva el valor vacío predeterminado del proyecto: la procedencia se
acredita mediante checkout exacto, hashes de fuente/clases y recibos del mismo build,
no mediante una marca de commit embebida inexistente.

```sh
NATIVE_TARGET=arm64-v8a "$GRADLE_HOME/bin/gradle" \
  --no-daemon --console=plain --max-workers=2 -Pkotlin.incremental=false \
  -PflexygramBetaDevelopment=true :TMessagesProj:assembleBetaDevelopmentDebug
```

Este comando requiere el overlay unsigned existente y las variables SDK/JDK/Python/CMake/
Ninja y proxy registradas; por sí solo no sustituye esa preparación.

**BUILD SUCCESSFUL,11m33s,248 tareas:192 ejecutadas,52 de caché,4 al día.**
JNI principal y Chaquopy reales, sin SKIP. Se conservaron1833 órdenes de compilación
(1832 fuentes únicas); único target nativo principal `aarch64-none-linux-android24`.

| Campo | Resultado |
|---|---|
| SHA256 APK | `9513d49706a714d496b45aab1992c0cc250e8c2e4df8bb1a1be00d8451e60ede` |
| Tamaño |113101251bytes |
| Application ID |`io.github.jose22yt.flexygram.beta.development` |
| Versión |13.0.2(1261) |
| ABI instalable |arm64-v8a |
| minSdk / target / compilación |24 /36 /37 |
| Firma |ausente |
| Ejecución Android |no realizada |

No se sobrescribe la beta histórica ni se exige coincidencia con su hash. La nueva APK
incluye los helpers BetaSystemBack/Api33/BetaPostInit en DEX y la Activity compilada
invoca los helpers nuevos. [Procedencia](evidence-pr29-build/beta-code-provenance.json).

## Verificador integrado sobre este binario

Gate PR25/PR23 real: **BETA_UNSIGNED_STATIC_REVIEW_ONLY_PENDING_ANDROID**.

- ZIP/CRC, identidad/versión, clases BuildConfig del mismo build, DEX y zipalign16KB pasan.
- Sin INTERNET; permisos sólo ACCESS_NETWORK_STATE y receptor dinámico propio protegido
  por firma. Se conserva ApplicationLoader y el único launcher público esperado.
- API ID0/hash vacío; seis capacidades false, push/configuraciones externos desactivados.
- 97 ELF detectados:96 ARM64, **96/96 pasan condiciones4KB/16KB**; un payload no objetivo
  se conserva sin presentarlo como ABI Android válido. Cero dependencias ausentes,
  símbolos fuertes sin resolver o versiones incompatibles; cuatro ELF experimentales
  tienen hashes exactos aprobados.
- Tres guardas JNI (ConnectionsManager y apertura de sockets) contienen sólo RET;
  .text empaquetizada coincide con la biblioteca enlazada. SHA256 JNI empaquetizado
  `341bda8e40cd6a457c9754bbba205aed83e2d926047a929f47c5287957a7e362`.
- Escáner dirigido:14858 entradas/7 archivos anidados, cero hallazgos vigilados. No
  certifica ausencia universal de secretos. Ninguna clave real añadida.

[Gate completo](evidence-pr29-build/beta-final-gate.json) ·
[guardas](evidence-pr29-build/beta-native-linked-guards.json) ·
[68 IDs y resultados](evidence-pr29-build/results.json).

Warnings heredados conservados: deprecaciones Kotlin/Java/CMake/WebRTC, recursos sin
default y libjnidispatch.so empaquetada sin strip. No se eliminan bibliotecas/funciones
para silenciarlos. No son por sí solos un crash demostrado. Log completo saneado
[comprimido](evidence-pr29-build/gradle-beta-unsigned-attempt2.log.gz), con
[hashes](evidence-pr29-build/build-log-hashes.json) y
[resumen de tareas](evidence-pr29-build/gradle-beta-unsigned-attempt2-tasks.log).

## Respaldo preparado: todavía local

ZIP privado nuevo con APK, clases del mismo build, JNI sin strip, compile_commands,
insumos nativos exactos, recetas y evidencias.40 miembros;337741135bytes.
SHA256`812ef5f9132edb75d0f061d8db9058489309194ea183bba5cef6dfbd6765029d`.
Todos los hashes/CRC comprobados y herramienta integrada archive.py inspect aprobada.
**Esto no demuestra conservación persistente ni recuperación remota.**

Destino propuesto:
`/FlexyGram-Work2-Private/FlexyGram-BetaDevelopment-PR29-97dfb08-Unsigned-Private.zip`.

La prueba sintética previa de Dropbox subió y recuperó57671850bytes con SHA exacto;
esta sesión confirmó que sigue listada. La aprobación anterior cubría carpeta y prueba
sintética. Según la condición del responsable y el relevo Work1, antes de subir APK se
requiere aprobar el acceso privado a la carpeta: miembros e invitaciones. Las herramientas
expuestas no los enumeran; los metadatos no acreditan por sí solos exclusividad.
**No se subió este respaldo ni se generó un enlace compartido.**

Una vez confirmado ese acceso y la subida del archivo exacto: subir sin sobrescribir,
recuperar mediante enlace temporal de un uso y comprobar SHA/CRC/miembros/APK/clases.
No hace falta otra compilación. Firma, clave/custodia, entrega e instalación siguen
requiriendo autorizaciones independientes. No se incluyen claves en el ZIP.

Faltan pruebas reales de arranque, UI sintética/Back/lifecycle, carga JNI/Python, exportación,
restauración sintética y páginas de memoria medidas en Android. No se midió rendimiento.
Main/develop intactas; ningún PR se fusionó a ellas. Sin autenticación, servicios remotos,
Production, Actions, firma, instalación, distribución o Paso4.
