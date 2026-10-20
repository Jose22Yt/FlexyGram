# P0.4c — Revisión independiente del candidato unsigned reconstruido (2026-10-20)

## Alcance y resultado permitido

Se incorpora tests/native_compatibility/review_rebuilt_candidate.py para la APK
Diagnostic sin firma reconstruida por Work. No sustituye al histórico
ddb7b017838a2a13991ac09154bbf252a11d62326e9a588349ca03c115e01699
ni modifica review_unsigned_contract.py, contrato v1 o verify_post_sign_diagnostic.py.

Referencia fija del candidato:

- Fuente compilada: 1177ceb8f4351b1626dd65e3dbd657f3b0ff159f.
- APK: flexygram-v13.0.2(1261)-diagnostic-debug-unsigned.apk.
- Tamaño: 113080183 bytes.
- SHA256: 291881863ea81418fa6cb12104b6eaea4aee2403822894da2143a51f3030bdd5.
- JNI ARM64 diferente: lib/arm64-v8a/libtmessages.49.so;
  SHA256 756e53d23f29ecca32d7c9706375494cdf2217d0db8d314a4195d0174400912b.

### Fase A: recibos públicos (sin APK privada)

El verificador enlaza el inventario de 44 archivos con el objeto Git exacto
d668ab49458669e0ca5fc63102d8b19653e373e8 de
evidence-unsigned-rebuild-20261020/evidence-sha256.json.
Para cada archivo comprueba tamaño y SHA256. Compara de manera independiente:
HEAD de fuentes, ejecución Gradle, APK y políticas Diagnostic, 97 entradas ELF,
96 AArch64 con controles estáticos 4/16KB/API24, cuatro ELF reconstruidos exactos,
un solo cambio de hash ELF frente al inventario histórico (JNI),
tres guardas RET, 231 resultados históricos de Work por modalidad,
ausencia de firma/instalación/Android y respaldo privado indicado en el recibo.

Comando desde la raíz del checkout completo:

    python3.11 -B tests/native_compatibility/review_rebuilt_candidate.py

Salida exitosa: CANDIDATE_METADATA_REVIEWED_BYTES_NOT_VERIFIED.

**Esta salida no certifica la existencia, identidad o contenido del APK físico.**
Una copia alterada de los 44 recibos, un índice diferente o una contradicción
en la procedencia devuelve BLOCKED con código de salida 1.

### Fase B: bytes privados reales (obligatoria para revisar el candidato)

Recuperar el respaldo privado comprobado por Work y extraer el APK en un directorio
privado no enlazado simbólicamente; no adjuntar binarios ni claves a GitHub o chat.
Ejecutar:

    python3.11 -B tests/native_compatibility/review_rebuilt_candidate.py --apk '/ruta/privada/flexygram-v13.0.2(1261)-diagnostic-debug-unsigned.apk'

Además de la Fase A exige los bytes reales: nombre, tamaño, SHA256, CRC,
miembros y tipos de ZIP, ausencia de firmas APK/JAR, inventario de 97 ELF
(30 en APK, 19 en requirements-common, 48 en stdlib), los 97 SHA256 físicos,
arquitectura y PT_LOAD real 16KB por cada AArch64. Un miembro distinto,
extra o ausente bloquea la revisión.

Salida exitosa: CANDIDATE_BYTES_STATICALLY_VERIFIED_PENDING_ANDROID.

**Esta salida sigue sin equivaler a una ejecución Android ni aprobar una firma.**
La prueba de ZIP alignment publicada fue efectuada por Work; ante necesidad
de nueva evidencia, reejecutar zipalign -c -P 16 -v 4 contra los mismos bytes
privados. El código no modifica archivos, utiliza la biblioteca Python estándar
y no necesita cuentas ni conexión de red.

### Tests obligatorios añadidos

tests/native_compatibility/test_rebuilt_candidate_review.py aporta **24 tests
sintéticos** (sin APK real), incluyendo cambios de recibos, JNI, historial,
guardas, alcance prohibido, omisión de tests, ZIP, firma JAR, symlinks,
ELF 4KB-only, duplicados e inventario físico, más una vía positiva de 97 ELF.
El gate run_gate.py requiere ahora **255 tests mínimos**, sin omisiones,
fallos, errores o expectedFailure.

Comandos de Work:

    python3.11 -B -m unittest discover -s tests/native_compatibility -p test_rebuilt_candidate_review.py -v
    python3.11 -B -O -m unittest discover -s tests/native_compatibility -p test_rebuilt_candidate_review.py -v
    # En checkout con JDK21 y recursos externos PR20/21 fijados:
    python3.11 -B tests/native_compatibility/run_gate.py --output /private/native-255.json
    python3.11 -B -O tests/native_compatibility/run_gate.py --output /private/native-255-opt.json

Las rutas /private son ejemplos. Se necesitan las variables/archivos fijados
en WORK-CONTINUATION-2026-10-20.md. Las 24 regresiones se han **guardado
en GitHub, pero no ejecutado oficialmente desde este chat**. No contar como PASS
antes de la reejecución auténtica en checkout completo.

## Bloqueos y separación estricta de autorizaciones

No existe aprobación para generar claves, firmar, instalar, conectar Telegram,
usar dispositivos personales, distribuir ni habilitar Production. No iniciar
Paso 4, Actions, ni fusionar PR #17; main y develop permanecen intactas.

La API verify_post_sign_diagnostic.py actual sigue vinculada a su evidencia
unsigned histórica. **No utilizarla sin adaptación explícita y revisada a un
candidato firmado autorizado**. Custodia recuperable, autorización independiente,
identidad de certificado y contrato de laboratorio v2 son pasos futuros. Aun tras
una firma válida, faltan boot y 12/12 casos reales por perfil ARM64 API24/4KB
y API35/16KB estricto, con aislamiento offline realmente comprobado.

Este revisor permite adelantar el cierre del candidato **sin rehacer JNI,
Chaquopy, cuatro ELF, tres wheels o Gradle** ni confundir informes con ejecución.
