# P0.4c — revisión estática de la APK sin firma antes del contrato de laboratorio v2

Estado: **solo propuesta de datos sin firmar**. Este paso no firma, no instala, no distribuye, no genera claves, no reescribe el contrato v1 y no ejecuta Android. El PR #17 permanece en borrador.

## Qué se ha preparado aquí

- `tests/native_compatibility/review_unsigned_contract.py` lee **en modo solo lectura** las 44 evidencias publicadas por Work el 19 de octubre, fija previamente el SHA-256 del inventario (`fc57830ec457a0eb43d7250d853f267437c4fd8bda0c894e575e6d48c80405bc`) y recalcula los SHA-256 individuales y rechaza cualquier falta o alteración; revisa además inventarios, procedencia de las 18 wheels, 3 reconstruidas, 4 ELF, hashes idénticos A/B y empaquetado, 96 ELF ARM64, controles estáticos 4/16 KB, guardas JNI, Diagnostic sin INTERNET, bloqueo de Production y falta de ejecución Android.
- Protege el contrato original `tests/native_compatibility/android_lab/contract.json` comprobando que todavía identifica la APK **histórica firmada**, distinta de la APK nueva sin firma; comprueba también `signing-v2/identity.pending.json`, que debe continuar bloqueado y sin certificado real.
- Su salida JSON es `UNSIGNED_EVIDENCE_REVIEWED_SIGNING_BLOCKED` con valores de `signed_apk_sha256`, `certificate_sha256` y `signed_runner_sha256` **null**. **No** se permite usar esa salida como `contract.json` del runner ni como prueba de firma, carga JNI o compatibilidad Android.
- `tests/native_compatibility/test_unsigned_contract_review.py` añade **12 pruebas host**, incluidas mutaciones negativas para evidencias, certificados/firmas, permiso INTERNET, ABI y falsos PASS. El nuevo código está dentro de `tests/native_compatibility/` para conservar intacta la protección `scope_native`. No se amplió `reviewed_changes.json` ni se modificaron archivos activos.

**Límite de verificación:** en este entorno no se ejecutó todavía la nueva suite completa de pruebas Python del checkout. Las 279 pruebas de Work corresponden al commit anterior; **no** atribuirles estas 12 nuevas pruebas hasta reejecutarlas.

## Comandos para Work — primero estos, antes de preparar un contrato firmado

```sh
python3.11 -B tests/native_compatibility/review_unsigned_contract.py
python3.11 -B -O tests/native_compatibility/review_unsigned_contract.py

python3.11 -B -m unittest discover -s tests/native_compatibility -p test_unsigned_contract_review.py -v
python3.11 -B -O -m unittest discover -s tests/native_compatibility -p test_unsigned_contract_review.py -v

python3.11 -B tests/native_compatibility/run_gate.py --output /private/native-latest.json
python3.11 -B -O tests/native_compatibility/run_gate.py --output /private/native-latest-optimized.json
```

Cada comprobación debe salir 0 y las suites no pueden tener fallos, omisiones ni falsos éxitos. El gate host previo de 177 casos debería aumentar en 11 si el descubrimiento los incluye; validar el total real, sin dobles cómputos. El verificador solo confirma la coherencia de **registros publicados**, no sustituye volver a leer la APK binaria original desde almacenamiento privado y recalcular su SHA-256.

## Orden para destrabar laboratorios

1. Work ejecuta los nuevos tests y corrige errores verdaderos sin relajar controles, conservando las evidencias originales. Audita el APK binario privado SHA256 `ddb7b017838a2a13991ac09154bbf252a11d62326e9a588349ca03c115e01699` (113080783 bytes). Si no está disponible, **BLOCKED_MISSING_APK**; no regenerar una APK diferente y fingir que es idéntica.
2. Obtener el recurso de custodia **recuperable** previsto en `signing-v2/PLAN.md`. **Generación de clave Diagnostic previamente autorizada**, pero solo cuando se demuestre custodia segura, sin compartir secretos por chat. Ninguna firma autorizada todavía.
3. Preparar revisión explícita del nuevo contrato **v2 separado** a partir de mediciones reales; nunca editar los pins del contrato v1 para hacer aceptar otra APK. El SHA del APK firmado se debe medir después de la firma; no sirve reutilizar el SHA del APK sin firma. El runner y la APK Diagnostic deberán firmarse con el certificado revisado que corresponda.
4. Solo con aprobación separada para firmar, avanzar a ensayo en dos emuladores aislados ARM64 (API24/4096 y API35+/16384 real y estricto), sin cuentas personales ni conexión externa. Ejecutar los 12 casos reales por perfil y guardar hashes, logs y counters para revisión.

**No** fusionar PR17, activar Actions, modificar Production, iniciar Paso 4, permitir autenticación, ni publicar APK/keystore. Las pruebas en dispositivos son una autorización y una puerta separadas.
