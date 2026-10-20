# P0.4c — continuación verificable y puerta de contrato de laboratorio v2

**Estado: pre-laboratorio.** No se ha firmado una APK nueva, generado una clave, utilizado ADB, activado Production, fusionado PR17 ni iniciado Paso 4. Todos los cambios se limitan a `tests/native_compatibility/` y documentación.

## Lo que quedó implementado desde ChatGPT

1. `verify_private_unsigned_apk.py` (existente): comprueba contra la APK física privada, con SHA de origen fijo, 97 ELF y PT_LOAD 16 KB.
2. `verify_post_sign_diagnostic.py` (**nuevo**): preparado para ejecutarse **solamente después de una firma Diagnostic autorizada**. Exige el APK fuente unsigned verificado, una identidad/custodia privada revisada, certificado SHA-256 fijado, `apksigner verify --min-sdk-version 24`, APKv2 válido, un solo certificado, y equivalencia de todos los miembros ZIP descomprimidos no pertenecientes a la firma entre las APK unsigned y signed. Devuelve `SIGNED_STATIC_REVIEW_ONLY_PENDING_ANDROID` — no instala, distribuye, declara runtime ni modifica contratos. El expediente de aprobación es metadato: debe verificarse fuera de este script mediante revisión humana; editar un JSON no constituye autorización auténtica.
3. `create_lab_v2_draft.py` (**nuevo**): prepara un **borrador no ejecutable** de un contrato futuro v2 usando las 44 evidencias originales aprobadas y el contrato histórico v1 inalterado. Copia nombres de casos, wheel hashes, cuatro ELF, alcance Diagnostic y obtiene el hash del JNI realmente empaquetado según la auditoría. Conserva `certificate_sha256`, APK firmado y runner firmado en `null`. Nunca emite un contrato que `run_lab.py` acepte. Si se solicita escribir, exige destino privado nuevo fuera del checkout y permisos 0600.
4. `test_post_sign_diagnostic.py` aporta **11 pruebas sintéticas** contra certificados incorrectos, doble firmante, esquema APKv2 ausente, autorización/custodia inválida y cambios del manifiesto/recursos.
5. `test_lab_v2_draft.py` aporta **14 pruebas sintéticas** de procedencia, JNI, omisiones, salida privada y bloqueo de firma.

Las **25 pruebas nuevas (11+14)** de firma posterior y borrador v2 se ejecutaron **en una reproducción local del código** con Python 3.13.5, normal y `-O`; junto con las nueve pruebas sintéticas del APK físico, el total local comprobado es **34/34 por modalidad**. Esto no es la suite oficial del checkout. **No** implica ejecución de la suite oficial del checkout, Python 3.11, ni verificación de la APK privada.

## Comandos para Work, en orden

### Ahora — sin firmar, sin compilar de nuevo si no hace falta

```sh
python3.11 -B -m unittest discover -s tests/native_compatibility -p test_unsigned_contract_review.py -v
python3.11 -B -m unittest discover -s tests/native_compatibility -p test_private_unsigned_apk.py -v
python3.11 -B -m unittest discover -s tests/native_compatibility -p test_post_sign_diagnostic.py -v
python3.11 -B -m unittest discover -s tests/native_compatibility -p test_lab_v2_draft.py -v
python3.11 -B tests/native_compatibility/run_gate.py --output /private/p04c-host-225.json
python3.11 -B -O tests/native_compatibility/run_gate.py --output /private/p04c-host-225-optimized.json

python3.11 -B tests/native_compatibility/review_unsigned_contract.py
python3.11 -B tests/native_compatibility/create_lab_v2_draft.py --output /private/p04c-lab-v2-draft-new.json
python3.11 -B tests/native_compatibility/verify_private_unsigned_apk.py \
  --apk '/private/apks/flexygram-v13.0.2(1261)-diagnostic-debug-unsigned.apk'
```

`/private` es un ejemplo: Work debe usar rutas privadas reales existentes, con su APK original intacta. Exigir **225 o más casos**, cero fallos/omisiones y ambas modalidades. El gate host falla si descubre menos de 225 casos. Registrar hashes privados y logs sin publicarlos si contienen binarios/secretos.

### Después, únicamente si el propietario verifica custodia y **autoriza expresamente la firma**

```sh
python3.11 -B tests/native_compatibility/verify_post_sign_diagnostic.py \
  --unsigned-apk /private/apks/original-diagnostic-unsigned.apk \
  --signed-apk /private/apks/new-diagnostic-signed.apk \
  --identity /private/approved-signing-record.json \
  --apksigner /private/android-sdk/build-tools/36.0.0/apksigner
```

Los nombres de archivo de arriba son **ejemplos** y deben sustituirse por los artefactos medidos. La identidad debe proceder de revisión autorizada y custodia recuperable probada; **no** crear un JSON arbitrario que afirme aprobación. Sin permiso de firma, **no ejecutar la etapa post-signing**, ni escribir un certificado falso o generar claves.

Después de una revisión post-firma real: crear un contrato v2 **separado**, reconstruir/fijar y firmar el runner con certificado aceptado, actualizar la validación PR20/21 sin cambiar sus pins v1 históricos, disponer de dos laboratorios ARM64 aislados con 4 KB y 16 KB estrictos, ejecutar **12 casos reales por perfil**, y revisar logs/counters. Ningún PASS host habilita Production ni distribución.

**No hay autenticación, red, dispositivos personales, claves o APK firmadas nuevas en esta continuación.**
