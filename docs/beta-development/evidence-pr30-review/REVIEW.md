# Work2 — revisión ejecutada del verificador postfirma Beta

Responsable del proyecto: @Lukhou23. PR30 revisado: `2ab7546b0fddf52890d3ae45eaef599358b861cd`. Revisión en checkout independiente, sin modificar la rama de Work1 ni integrar PR30. PR23 permanece abierto y en borrador.

## Resultados reales

Python 3.11.17:
- tests/beta_post_sign: **15/15 normal; 15/15 con -O**, cero omisiones.
- tests/beta_handoff: **21/21 normal; 21/21 con -O**, cero omisiones.
Son 36 métodos distintos; las ejecuciones optimizadas no se suman como casos nuevos.
Los 15 casos son ZIPs sintéticos y dobles de herramientas. No generan claves, certificados o firmas. El warning de entrada ZIP duplicada pertenece al caso negativo esperado.
Los cuatro logs adyacentes conservan las ejecuciones.

Revisión de código: vincula autorización Beta específica, certificado, hash de unsigned y recibo/clases; exige un solo firmante, v2 para minSdk24, payload constante, manifiesto offline y alineación. Rechaza autorizaciones Diagnostic. No se halló fallo demostrado que requiera parche. No se han debilitado controles ni sustituido los verificadores compartidos. Sólo tres archivos nuevos en PR30; gate.py, review_apk.py y primitivas históricas coinciden con PR23.

**Gate PR25 ejecutado nuevamente sobre APK real, desde checkout PR30: PASS**
`BETA_UNSIGNED_STATIC_REVIEW_ONLY_PENDING_ANDROID`.
Manifiesto idéntico al informe original, BuildConfig cerrado, zipalign16KB true, lista de bloqueos nativos vacía. No recompilación.
Herramientas reales: BuildTools36.0.0/aapt2/zipalign/apksigner, NDK27.2.12479018, javap JDK21.0.10.
apksigner verify --verbose --print-certs --min-sdk-version24: rechazo esperado de unsigned, exit1, DOES NOT VERIFY / Missing META-INF/MANIFEST.MF. zipalign -c -P16 4: exit0.
No se ejecutó el camino positivo postfirma contra una APK firmada real: está prohibido firmar en esta etapa. No se declara aprobado ese resultado ni funcionamiento Android.

## Entradas del mismo build preservadas

- Código compilado: `97dfb08e58159b31d322dd8435080fb039abdeb9`.
- Paquete: io.github.jose22yt.flexygram.beta.development; 13.0.2 (1261).
- Unsigned: 113101251 bytes; SHA256 `9513d49706a714d496b45aab1992c0cc250e8c2e4df8bb1a1be00d8451e60ede`.
- ZIP privado original: 337741135 bytes, 40 miembros; SHA256 `812ef5f9132edb75d0f061d8db9058489309194ea183bba5cef6dfbd6765029d`.
Ambos hashes comprobados otra vez sin modificarlos; respaldo remoto previamente recuperado y verificado, revisión Dropbox0165e4a928401c700000003314317a1. No se reescribió ni volvió a subir.
- Inventario post_sign.class_inventory: **15143 archivos**, igualdad completa con same-build-classes.zip. No mezcla de clases de otra compilación.
- Informe unsigned original: SHA256 `32821104c3a601a6283928a58cd793bdbfb46587ef306f3ae1f1c5d3a4b502d8`.
- Recibo de build privado generado con el esquema PR30, sin autorización: SHA256 `7cb0c40b1ef683d15d32f92dbc6d78a3916e4762461407ae68662d4b8a288e32`.
Ese JSON contiene el mapa completo clases->SHA, paquete, commit, versiones y hashes de APK/informe. Es reproducible con los insumos del ZIP; la copia nueva local no se presenta como respaldada remotamente.
No se creó signing-approval.json ni se fijaron estados de custodia de clave a true.

## Pasos exactos antes de una primera firma

1. Aprobar generación de **identidad Beta personal offline** exclusiva, distinta de Diagnostic/Production/Exteraless. No se reutiliza autorización histórica de clave Diagnostic.
2. Acordar custodio, host autorizado, almacenamiento del keystore y copia cifrada recuperable. La autorización de Dropbox para APK **no** autoriza almacenar una clave. La contraseña debe conservarse separada y existir un canal de entrada local protegido: nunca chat, argv, repositorio, logs ni variables impresas. No se ha verificado ni creado ese canal/custodia.
3. Tras esa autorización, generar la identidad en el host acordado (propuesta a aprobar: RSA3072/SHA256, keystore protegido y exclusivo). Crear copia cifrada privada; recuperarla a ubicación independiente y abrirla mediante entrada protegida. Verificar certificado DER/huella SHA256 igual y borrar sólo temporales autorizados. Registrar sólo huella/algoritmo/fecha/identificador y procedimiento; no publicar keystore/contraseñas/certificado en GitHub.
4. Preparar/restaurar las 15143 clases del ZIP, el informe unsigned original y recibo con el hash indicado; volver a verificar sus bytes. Aprobar **separadamente la firma** del unsigned SHA9513d497… y recibo SHA7cb0c40b… con la nueva huella, scope FlexyGram_Beta_personal_offline_only y referencia comprobable de la decisión. Rellenar el registro de autorización sólo después de verificar custodia y recibir esa decisión.
5. Firmar **una copia nueva**, nunca el unsigned original ni su ZIP. Herramientas fijadas, un solo firmante, v2 activo para API24; evitar introducir v1 innecesariamente porque un MANIFEST.MF preexistente debe permanecer idéntico. No modificar ni zipalign después de firmar: cualquier alineación necesaria va en una copia previa a firma. No compilar de nuevo si los mismos bytes pasan.
6. Calcular nuevo SHA de signed. Guardar en destino privado autorizado **nuevo** y recuperar a ruta distinta; comprobar SHA/CRC/identidad, sin sobrescribir archivo unsigned. El respaldo signed contendrá una sola APK para ser compatible con archive.py.
7. Ejecutar post_sign.py con unsigned, signed y recovered distintos; recibo y aprobación reales; clases del mismo build; informe previo y herramientas fijadas. Salida0 y estado BETA_SIGNED_STATIC_REVIEW_ONLY_PENDING_ANDROID son obligatorios, además del recibo separado de transferencia real. La herramienta no prueba la recuperación remota por sí sola.
8. Presentar huella, ambos hashes y resultados antes de pedir autorización independiente de entrega/instalación/prueba. Ninguna firma concede permiso de instalar. Arranque/JNI/Python/UI, 4KB/16KB y Android17 continúan pendientes de ejecución real.

Invocación futura (no ejecutada; entradas inexistentes de signed/approval no se fabrican):

```sh
python3.11 tools/beta_handoff/post_sign.py \
  --unsigned-apk /private/beta/unsigned.apk \
  --signed-apk /private/beta/signed.apk \
  --recovered-apk /private/recovered/signed.apk \
  --unsigned-sha256 9513d49706a714d496b45aab1992c0cc250e8c2e4df8bb1a1be00d8451e60ede \
  --signed-sha256 "$BETA_SIGNED_SHA256" \
  --commit 97dfb08e58159b31d322dd8435080fb039abdeb9 \
  --version-code 1261 --version-name 13.0.2 \
  --classes /private/beta/classes \
  --unsigned-review /private/beta/unsigned-review.json \
  --build-receipt /private/beta/build-receipt.json \
  --approval /private/beta/signing-approval.json \
  --build-tools /sdk/build-tools/36.0.0 \
  --ndk /sdk/ndk/27.2.12479018 --javap /jdk21/bin/javap \
  --output /private/reports/post-sign-NEW.json
```

Límites: recibos/JSON son declaraciones revisadas, no firmas de autorización; commit no deducible del APK. No hay prueba de firma real positiva, Android, instalación ni rendimiento. No se generaron claves ni se firmó/instaló/distribuyó. Main/develop y ramas Work1 intactas. Sin autenticación, Telegram, Production, Actions ni Paso4.
