# Firma temporal Beta: política implementada, sin identidad generada

Proyecto dirigido por @Lukhou23. Trial único:
`flexygram-personal-offline-9513d497-v1`.

## Alcance fijo

- Unsigned SHA256: `9513d49706a714d496b45aab1992c0cc250e8c2e4df8bb1a1be00d8451e60ede`.
- Código compilado: `97dfb08e58159b31d322dd8435080fb039abdeb9`.
- Paquete: `io.github.jose22yt.flexygram.beta.development`, 13.0.2 (1261).
- Exclusivamente primera prueba personal offline, sin promesa de actualizaciones.

El verificador es de sólo lectura: no genera secretos, no firma, no instala ni
efectúa transferencias. Identificar un trial no hace cumplir físicamente una única
instalación ni autentica al autor de un JSON. Las decisiones humanas y evidencias
de la operación siguen siendo obligatorias. Repetir una verificación del mismo
binario no autoriza otra prueba ni amplía el alcance.

## Implementación y separación

Se incorporan desde PR30 `2ab7546b0fddf52890d3ae45eaef599358b861cd` el
verificador y sus 15 pruebas. La rama Work1 no se modifica.
`post_sign.approval` mantiene intactas sus condiciones permanentes, incluida la
custodia recuperable. Se añaden únicamente parámetros internos de delegación a
verify/run_cli; la CLI permanente no ofrece un interruptor temporal.

`temporary_post_sign.py` tiene su propia aprobación y estado de resultado. Reutiliza
el mismo motor: gate PR25, firma v2/API24 y firmante único/huella aprobada,
inventario y CRC, manifiesto offline, DEX/recursos/JNI/Chaquopy, clases y recibos
vinculados, alineación 4K/16K y comprobaciones nativas, hashes finales e informe
nuevo exclusivo 0600. No elimina verificaciones para conseguir un PASS.

El contrato temporal rechaza campos desconocidos, incluidos los de custodia
permanente aunque sean false. Exige generación temporal previamente autorizada,
revisión del canal de entrada y autorización posterior de firma. Las tres
referencias son declaraciones revisadas, no pruebas criptográficas de permisos.

También exige `--recovery-receipt` con schema1, trial_id exacto,
status PRIVATE_SIGNED_APK_RECOVERY_VERIFIED, provider Dropbox,
independently_downloaded true, signed_apk_sha256, bytes, file_id, revision y
verification_reference. Debe corresponder a una descarga real observada por el
operador, distinta de una simple copia local. Sus bytes se comprueban antes y
después. El informe conserva remote_recovery_independently_observed=false porque
el programa no efectúa la transferencia; sólo valida la declaración vinculada.

## Pruebas realmente ejecutadas

Python3.11.17:
- 15 permanentes +14 temporales: 29/29 normal, 29/29 -O, cero omisiones.
- Compatibilidad beta_handoff: 21/21 normal y 21/21 -O, cero omisiones.
- Total: 50 métodos distintos, no 100 por contar ambos modos.

Los tests usan ZIPs y herramientas sintéticas. Para probar la ruta temporal con
el SHA fijo de una APK real, sólo la consulta SHA del unsigned ficticio utiliza
un oráculo explícito. No se altera el hash real de ningún artefacto ni una
constante de producción. Otros hashes, CRC e inventarios se calculan de verdad.
Una regresión sin ese oráculo demuestra que el unsigned sintético se rechaza.
El gate real de la APK se ejecutó en la revisión previa; no se repite esa auditoría
porque sus archivos/dependencias y bytes aprobados no cambiaron.

Pruebas negativas: identidad/pines/versiones, contrato permanente/Diagnostic,
custodia simulada, autorizaciones, certificado distinto/varios firmantes/v2
inválido, payload y manifiesto, nativos/clases, copia recuperada, recibo remoto
ausente/mal vinculado/modificado, informe exclusivo y tipos booleanos estrictos.

`probe_password_channel.py` se ejecutó realmente contra Java21.0.10: fixture
PUBLICO por pipe stdin, sin incluirlo en argv/environment, sin console/PTY y con
core dumps desactivados en el hijo. Sólo crea un fuente Java público temporal.
También prueba el lector real de keytool con -storepass:file /proc/self/fd/0,
exclusivamente -list sobre un keystore inexistente; el control negativo con
archivo de contraseña inexistente falla durante lectura. Ambos exit1 son
esperados y diferenciados: no son verificaciones de firma. No abre ni crea un
keystore real, no genera contraseñas/claves/certificados,
no firma y no certifica custodia ni protección contra administrador/inspección de
memoria/artefactos de crash JVM. Logs y resultado adyacentes.

## Procedimiento pendiente, antes de generar nada

1. Revisar esta política y autorizar **sólo generación temporal** RSA3072,
   identidad exclusiva del trial y certificado SHA256withRSA. No heredar la
   identidad Diagnostic/Production/Beta permanente ni certificados históricos.
2. Preparar el worker de generación: contraseña aleatoria creada dentro del
   proceso, nunca devuelta al modelo; envío a keytool por canal stdin/descriptor
   protegido sin secretos en código de herramientas, argv, environment o archivos
   de texto. Descartar stdout/stderr no públicos, sin trazas de secretos; reportar
   sólo errores saneados y certificado/huella pública. Nada de contraseñas por chat.
   El lector exacto de contraseña de keytool ya fue comprobado con fixture
   público y control negativo, sin keystore; repetir ese preflight al iniciar
   el worker antes de usar material real.
3. Keystore cifrado temporal fuera de Git en directorio0700/archivo0600; contraseña
   retenida únicamente en memoria del proceso privado mientras se espera la
   siguiente autorización. Esto NO es custodia permanente ni recuperable.
   Si muere el proceso/se limpia Work, detenerse: no reconstruir ni fingir la misma
   identidad. Cualquier nueva generación/huella debe ser autorizada de nuevo.
   No iniciar este worker ni generar secretos con la autorización actual.
4. Presentar huella y solicitar **después** autorización específica de firma del
   unsigned y recibo de build revisados, con esa huella. Crear registro real de
   firma sólo tras esa decisión; el borrador no es una autorización.
5. Firmar una copia nueva con v2/API24. Preservar original y ZIP históricos; si
   hiciera falta alinear una copia, hacerlo antes de la firma. No recompilar ni
   cambiar dependencias, cliente, manifiesto, autenticación o capacidades.
6. Autorizar destino privado nuevo para la APK firmada, subir y descargarla de
   forma independiente, registrar hash/tamaño/ID/revisión y CRC. No usar carpeta
   KeyCustody ni guardar allí clave/contraseña. No modificar el respaldo unsigned.
7. Ejecutar temporal CLI con todas las opciones PR30 más --recovery-receipt.
   Requiere salida0/estado BETA_TEMPORARY_SIGNED_STATIC_REVIEW_ONLY_PENDING_ANDROID.
   No acredita instalación, arranque, JNI/Python real ni Android17/16KB.
8. Solicitar autorización independiente para entregar/instalar/probar. Tras la
   prueba, descartar identidad temporal bajo el procedimiento aprobado; no
   afirmar borrado seguro del host o que ya ocurrió porque el informe lo exige.

La contraseña no se envía a un gestor porque esta opción es descartable; si se
quiere preservar la identidad se debe detener y volver a la política permanente.
Con otra firma y el mismo paquete, no se promete actualización directa: sin una
migración de firma diseñada, habrá que desinstalar temporal e instalar la estable.
Eso borra datos privados locales; exportar antes diagnósticos sintéticos necesarios.
No afecta a Telegram/Exteraless, que tienen paquetes distintos.

## Estado de la autorización actual

Sólo implementación/pruebas de política. Ninguna clave, keystore, contraseña,
firma, distribución o instalación autorizada. La carpeta KeyCustody sigue vacía;
sus miembros/invitaciones/herencia no se han podido verificar completamente.
La APK original y ZIP conservan SHA9513d497… y SHA812ef5f9… respectivamente.
No se afirma recuperación permanente de los ficheros nuevos del workspace.
El código y evidencias se conservan en Git; los binarios no se publican allí.

Fuentes técnicas ya consultadas:
https://developer.android.com/tools/apksigner
https://developer.android.com/studio/publish/app-signing
