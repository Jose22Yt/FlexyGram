# Segunda APK offline: CRASH-001, compilación y verificación reales

Proyecto creado y dirigido por @Lukhou23. Código validado y realmente compilado:
**`2d532562f68946a83f5cdd2fc1059e3024beb525`**, HEAD de PR33 solicitado.
Se conserva el último ajuste del simulador al reconstruir la vista anterior;
no se vuelve a aa23afdc ni se integra PR32. Esta continuación no necesitó
cambios funcionales: sólo añade evidencias y actualiza el estado documental.
Un commit documental posterior no es otro commit de código compilado.

## Pruebas ejecutadas

Python3.11.17/JBR21.0.10, Groovy y CMake reales; Android con dobles explícitos:

| Suite | Métodos distintos | Normal | -O |
| --- | ---: | --- | --- |
| Beta, incluidas las nueve oficiales CRASH-001 |45|PASS|PASS|
| Importador personal |11|PASS|PASS|
| Handoff |21|PASS|PASS|
| Total sin duplicar modos ni repetir las nueve |77|PASS|PASS|

Las nueve también se ejecutaron de forma selectiva:9/9 normal y9/9 -O, cero
omisiones. Cubren abrir/volver sin cuenta, contenido sin JNI/Python disponibles,
25 ciclos, pulsaciones rápidas y Atrás en transición, temas, recreación,
imports aislados, insets/IME y tres cabeceras. Los logs/IDs y los77 métodos están
en [test-results.json](evidence-crash-001-build/test-results.json).
No se atribuye a estos tests una ejecución Android ni la reproducción del crash
del teléfono. La excepción original continúa desconocida.

## Recuperación necesaria, sin rehacer componentes verificados

El mantenimiento eliminó checkout, herramientas y archivos del workspace previo.
Se recuperó el ZIP privado aprobado desde Dropbox,337741135bytes/SHA812ef5f9…,
y se verificaron SHA/CRC antes de reutilizar sus insumos. Se restauraron18 wheels
originales,18 overlay y cuatro ELF exactos desde ese respaldo, sin recompilar los
cuatro ELF ni los tres wheels experimentales. No se descargaron imágenes Android.

Se recuperaron las herramientas fijadas: JDK21.0.10, Gradle9.7.1, NDK27.2.12479018,
SDK35/37.0, BuildTools36, CMake3.31.6, Ninja1.12.1 y Python3.11.17; checksums en
[toolchains.json](evidence-crash-001-build/toolchains.json). El paquete Ninja no
existía en pip con ese identificador; se recuperó su ZIP oficial1.12.1 con el hash
histórico, antes del build. No fue un fallo del código Android ni del build.
SDK37 se registró con el catálogo oficial y el android.jar aprobado intacto.
Se conservaron proxy/TLS, sin desactivar certificados ni eludir403.

Los16 submódulos se recuperaron en sus gitlinks fijados y se reutilizaron localmente
en el checkout aislado. Las dependencias activas y locks del repositorio no cambian.
Sólo el checkout local de build usa el overlay unsigned/experimental previamente
revisado: su SHA256 c91a190e… coincide con el de la primera compilación.

## Compilación real

`assembleBetaDevelopmentDebug`, ARM64, JNI y Chaquopy completos, sin SKIP nativo:

- **BUILD SUCCESSFUL en14m37s**, exit0; tiempo del wrapper877.56s.
-248 tareas:196 ejecutadas,52 de caché. Se conserva el uso real de caché, sin
  atribuir tareas recuperadas a compilaciones nuevas.
- buildChaquopyRuntimeArm64V8a ejecutado; chaquopy.so/libchaquopy_java.so compiladas.
- configureCMakeDebug[arm64-v8a]-2 y buildCMakeDebug[arm64-v8a]-2 ejecutadas.
-1833 órdenes nativas/1832 fuentes únicas; target aarch64-none-linux-android24.

[Log completo comprimido](evidence-crash-001-build/gradle-full.log.gz),
[resultado](evidence-crash-001-build/build-result.json),
[tareas nativas](evidence-crash-001-build/build-integrity.json).

No hubo fallo de Gradle que requiriera cambiar código. Advertencias heredadas de
deprecación, plural/recursos sin valor por defecto y libjnidispatch no strippeable
permanecen en el log; no se modificaron/eliminaron funciones para silenciarlas.

## APK nueva, sin firma

**FlexyGram-BetaDevelopment-CRASH001-2d532562-arm64-unsigned.apk**

- **113102119 bytes**.
- **SHA256 `2ca59f8f4575850d42b6fad56e231dbbbe2cff077fa93bf33aa3b638a3ae0d00`**.
- Paquete io.github.jose22yt.flexygram.beta.development,13.0.2(1261).
- ABI instalable arm64-v8a; min24/target36/compile37.
- Gate **BETA_UNSIGNED_STATIC_REVIEW_ONLY_PENDING_ANDROID**, exit0.
- Firma ausente: rechazo esperado de apksigner exit1/Missing META-INF/MANIFEST.MF;
  no es un APK firmado inválido ni un PASS de firma.

[Gate real](evidence-crash-001-build/apk-gate.json),
[procedencia](evidence-crash-001-build/apk-candidate.json).

BuildConfig cerrado, API ID0/hash vacío, capacidades externas y push deshabilitadas;
manifiesto offline sin INTERNET ni restauraciones de sesión, componentes,
identidad y DEX verificados. No se habilitó Production/autenticación/Telegram.

El bytecode real de Conversation instancia OfflineConversationView y no el renderer
de cuenta anterior; el de Activity invoca BetaSystemInsets.wrap. Ambas clases nuevas
están en DEX y sus hashes proceden de la misma compilación. Cada fuente Java beta
del build coincide con su blob del commit2d532562…. BUILD_COMMIT_ID conserva el
valor vacío del proyecto: la procedencia está en checkout/recibos/clases, no en
un stamp de commit embebido que no existe.

## ELF, JNI, Python y empaquetado

-97 ELF encontrados:96 ARM64,96/96 aptos estáticamente para4KB y16KB; un payload
  de otra arquitectura conservado y clasificado, no ABI Android instalable.
-0 DT_NEEDED ausentes,0 símbolos fuertes sin resolver y0 versiones incompatibles.
-Cuatro ELF reconstruidos históricos exactos; Python/lxml/Pillow y sus dependencias
  se conservaron, no se recompilaron ni eliminaron para ocultar alertas.
-Tres guardas JNI contienen exclusivamente RET y el .text empaquetado coincide
  con el enlazado. libtmessages empaquetada conserva SHA341bda8e… igual al build
  anterior verificado; el código nativo común no se modificó.
-zipalign16KB aprobado; manifiesto/recursos/DEX/JNI/Chaquopy íntegros.
-Escáner dirigido:14858 entradas/7 archivos anidados,0 hallazgos vigilados y0 errores.
  No certifica ausencia universal de secretos.

[Guardas enlazadas](evidence-crash-001-build/native-linked-guards.json).
Esto no demuestra carga ART/linker/Python en un teléfono4KB/16KB ni Android17.

## Nuevo respaldo preparado, todavía sólo local

**FlexyGram-BetaDevelopment-CRASH001-2d532562-Unsigned-Private.zip**
-337758546bytes,41 miembros.
-SHA256 **`9678e4d92b5b27e8018429be326a5345ce9c163b8b99cdb61424720f77fa5811`**.
-CRC y todos los SHA/tamaños internos verificados. Inspector PR25 de archivo
  existente ejecutado con éxito, leyendo todos los miembros y la APK única.
-Contiene sólo la segunda APK unsigned, clases del mismo build, JNI enlazada y
  órdenes de compilación, insumos nativos históricos, wheels/lock/overlay,
  recetas y evidencias. No incluye claves/keystores/contraseñas ni primera APK.
-No se subió ni se afirma conservación persistente/recuperación remota del nuevo ZIP.

[Recibo local](evidence-crash-001-build/private-bundle.json),
[inspección integrada](evidence-crash-001-build/bundle-inspection.json).

Ruta propuesta, pendiente de autorización específica:
`/FlexyGram-Work2-Private/FlexyGram-BetaDevelopment-CRASH001-2d532562-Unsigned-Private.zip`.
Después de autorizar: subir este archivo exacto, recuperar por separado y comprobar
hash/CRC/41 miembros/APK/clases/JNI. Nunca sobrescribir los respaldos anteriores.

La primera APK firmada remota conserva113163015bytes y revisión
0165e4b8d72b4f300000003314317a1. No se tocó ese archivo ni el ZIP unsigned anterior.

## Bloqueos de firma y prueba física

El proceso temporal16262 ya no existe tras el mantenimiento. No se recuperaron
su contraseña ni keystore, que por diseño no se subieron. No se generó identidad
nueva ni se firmó esta APK. La huella e68685ab… sigue siendo sólo referencia del
primer trial; un certificado público no recupera su clave privada.

La política temporal del primer trial fija hash9513d497…/commit97dfb08…: no se ha
repinado ni relajado para aceptar esta segunda APK. Antes de firmar hará falta
revisar un contrato separado de este candidato y autorizar identidad/custodia;
después, aprobar la firma del hash2ca59f8f… con una huella concreta. No reutilizar
la autorización de una sola firma del primer trial.

Con otra identidad y el mismo paquete no se promete actualización directa; sin
migración de firma diseñada, será necesaria reinstalación de la beta, que elimina
sus datos locales. Preparar antes la conservación de diagnósticos necesarios;
no desinstalar Telegram/Exteraless ni tocar datos personales para esta etapa.

Pendiente Android real: instalar sólo tras autorización, abrir conversación,
volver/repetir, pulsaciones/Atrás, temas, Activity/insets/rotación, JNI/Python y
ausencia de cierres. La causa exacta del crash anterior y la eficacia en el teléfono
no están confirmadas. No se exige ADB manual ni se inventan resultados de emulador.

Main/develop, PR23/primera APK y PR32 intactos; PR33 queda en borrador/sin fusionar.
Sin firma, subidas, distribución, instalación, Actions, Production ni Paso4.
