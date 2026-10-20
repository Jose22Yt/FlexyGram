# Primera firma temporal Beta — resultado real

Proyecto FlexyGram1.0, responsable @Lukhou23. Sólo firma local autorizada; sin subida de APK, entrega, distribución o instalación.

## Identidad y operación

Se comprobó antes de firmar que el proceso original seguía activo, con contraseña en memoria y el mismo keystore local. No se generó otra identidad.
Certificado SHA256 `e68685abf684405159d6d6edf93984f07f2043053c024f252888b9f55aee5e05`, RSA3072.
La contraseña pasó directamente de memoria del proceso a stdin de apksigner; no se incluyó en argv/environment/logs. No se publicó/subió clave, keystore o contraseña.

Código compilado: `97dfb08e58159b31d322dd8435080fb039abdeb9`.
Unsigned original:113101251bytes, SHA256 `9513d49706a714d496b45aab1992c0cc250e8c2e4df8bb1a1be00d8451e60ede`.
ZIP original SHA256 `812ef5f9132edb75d0f061d8db9058489309194ea183bba5cef6dfbd6765029d`.
Ambos hashes comprobados después de firmar y verificar: intactos. Respaldo Dropbox sin cambios.

Se copió el unsigned a un directorio local nuevo/exclusivo0700; se firmó a otro archivo, sin recompilación:
**FlexyGram-BetaDevelopment-97dfb08-OfflineTrial-Temporary-Signed.apk**
- Tamaño: **113163015 bytes**.
- SHA256: **`2a8d7a603cd49855534b41e31bf8296e9309ea8cc7e31e978215311a252ff825`**.
- Paquete: io.github.jose22yt.flexygram.beta.development,13.0.2(1261).
- Archivo local0600, no se adjunta ni distribuye.

## Verificaciones realmente ejecutadas

- BuildTools36/apksigner real: exit0, Verifies.
- Firma v2 true para minSdk24; un único firmante RSA3072, huella exactamente autorizada.
- v1/v3/v3.1/v4 false; no SourceStamp. No se exige igualdad del SHA del contenedor tras firmar.
- zipalign -c -P16 4: exit0. Comprobación4KB/16KB pasada.
- Motor PR30 ejecutado sobre bytes reales con la aprobación temporal separada: gate unsigned PR25, versiones/paquete, clases y recibos de mismo build, comparación integral de payload/CRC, certificado/v2, alineación y manifiesto firmado.
- **Payload idéntico:** manifiesto, DEX, recursos, JNI y Chaquopy sin cambios.
- Manifiesto offline preservado y sin INTERNET, capacidades externas cerradas.
-96 ELF ARM64 aceptados estáticamente,0 bloqueos;1 payload no objetivo conservado.
- Copia local de comparación leída y hash verificado. **No es recuperación remota.**
- No fallos de firma ni controles locales detectados.

El motor compartido se llamó con temporary_post_sign.approval, nunca con autorización permanente simulada.
Su resultado se etiqueta expresamente **BETA_TEMPORARY_LOCAL_CHECKS_PASSED_PENDING_PRIVATE_RECOVERY_AND_ANDROID**: no se presenta como aceptación de la política temporal completa.
Los campos installation_authorized/distribution_allowed/android_runtime_validated permanecen false.

## Estado de política completa y conservación

La CLI temporal completa se ejecutó y devolvió **BLOCKED, exit1**, porque no existe el recibo de recuperación remota firmado. El archivo de recuperación remoto está deliberadamente ausente; no se inventaron provider/file_id/revisión ni una descarga.
No se ha debilitado ni cambiado esa política para pasar el candidato. Los informes locales y el bloqueo completo se conservan adyacentes.

La APK firmada sólo tiene conservación local temporal por ahora. No se declara respaldo persistente ni recuperación privada confirmada. La identidad tampoco tiene custodia permanente: si se pierde el proceso/contraseña, detenerse, no generar otra sin permiso.

Siguiente autorización necesaria: subir **únicamente esta APK firmada** a
`/FlexyGram-Work2-Private/FlexyGram-BetaDevelopment-97dfb08-OfflineTrial-Temporary-Signed.apk`
y descargarla a otra ruta, verificar113163015bytes/SHA2562a8d7a60…/CRC, registrar ID/revisión y preparar recibo real. Antes de subir se revisará el estado de acceso disponible sin modificar permisos.
Después, ejecutar política completa con ese recibo y copia descargada. No sobrescribir ni modificar el ZIP/unsigned histórico.
Esta autorización de firma no concede esa subida ni la entrega/instalación; se solicita por separado.

No Android ejecutado: ni instalación, arranque, carga real JNI/Python ni rendimiento/16KB de dispositivo acreditados. Main/develop y Work1 intactos; PR23 sigue abierto en borrador. Sin autenticación/Telegram/servicios/Production/Actions/Paso4.
