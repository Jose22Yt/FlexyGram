# Conservación y recuperación de la identidad oficial

La generación ya fue confirmada por @Lukhou23. **No generes otra clave.** El procedimiento anterior de generación se conserva en el historial Git, pero no debe repetirse para este paquete. La identidad registrada está en [SIGNING.md](SIGNING.md).

El original PKCS12 y las contraseñas permanecen en el teléfono/control del propietario. El certificado público recibido por el asistente no acredita la existencia ni la restauración de dos backups; esa confirmación sigue pendiente.

## Verificar el original

Desde una terminal propia con Java, sin grabación ni registro de contraseñas:

```bash
java tools/signing/VerifySigning.java keystore /ruta/privada/flexygram-release.p12 5a598fb5ba42949b67b7c2635106fafd5f23179397e4c098757a73cd2d2ef66c
```

La contraseña se pide sin eco. El alias debe ser `flexygram-release`. Un PASS con POSSESSION_VERIFIED comprueba acceso y correspondencia clave/certificado en ese momento; no confirma soportes externos ni una APK.

## Dos backups cifrados y comprobados

La ruta guiada es [README_LOCAL.md](../tools/signing/README_LOCAL.md): `python3 tools/signing/owner_wizard.py`. La versión actual verifica y respalda el original oficial, sin generación. Nunca sobrescribe un backup existente. Si una clave falta, se detiene para recuperación.

Usa dos soportes separados bajo tu control y contraseñas fuertes en un gestor con recuperación independiente del teléfono. Dos carpetas del mismo dispositivo no son dos backups independientes. Cifra con age y verifica cada copia leyéndola desde su destino final. Si una nube no ofrece una ruta local, recupera una copia desde cada destino a carpetas de prueba distintas, y verifica esos archivos con el asistente local antes de confirmar. No envíes PKCS12, backups o contraseñas al chat o GitHub.

Para una recuperación manual, descifra a un nombre nuevo dentro del almacenamiento privado/cifrado del propietario, nunca encima del original, y repite la comprobación con la huella registrada. Si una copia no coincide, conserva el original y corrige el backup. No sustituyas la identidad.

## Confirmación de cierre

El propietario debe confirmar acceso al original y contraseñas, dos copias cifradas en soportes independientes y la recuperación de ambas desde sus destinos. El software solo comprueba los archivos accesibles; no prueba independencia física ni disponibilidad futura. El informe adjunto hasta ahora dice `private_key=NOT_CHECKED` y `custody=OWNER_CONFIRMATION_REQUIRED`; se ha registrado por separado la confirmación del propietario sobre acceso privado, sin convertirla en una inspección por el asistente.

## Actualizaciones y CI

Las futuras Beta conservarán paquete y certificado y aumentarán versionCode. No cambies la clave por versión. Su incorporación a Actions requiere autorización específica posterior y secretos protegidos, descritos en [SIGNING.md](SIGNING.md). No se han subido entradas privadas ni iniciado compilaciones.
