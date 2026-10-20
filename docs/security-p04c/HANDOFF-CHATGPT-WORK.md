# FlexyGram P0.4c — relevo operativo ChatGPT → Work

**Estado:** revisión host solamente; PR #17 sigue DRAFT y sin fusionar. No implica beta, firma ni validación Android.

## Cambios de código preparados en esta continuación

- `reproduce_locked_16k.py`: los 18 resultados deben corresponder uno a uno a los 18 inputs del lock. Se exigen los 3 wheel sustitutos aprobados, el nombre exacto de su wheel fuente (según evidencia revisada), el SHA-256 original y su URL registrada. Rechaza symlinks en rutas de ELF, wheels y manifest.
- `test_reproduce_locked_16k.py`: 10 casos de regresión añadidos sobre correspondencia, metadatos e inputs inseguros. Total actual de este archivo: **25 casos**.
- `stage_recovered_inputs.py` y sus pruebas mantienen verificación de hashes antes/durante el staging, manifest cerrado y detección de colisiones de ruta.
- `run_p04c_host_gate.py`: ejecutor de gate offline con Python 3.11 exacto, sin omisiones y con huellas SHA-256 de los scripts.

Las tres suites suman **52 casos descubiertos en el código**: staging 19, FreeType 8 y reproducción 25. **La suite completa aún no se ejecutó en Python 3.11 desde esta continuación.** Se ejercitaron localmente 12 escenarios focalizados en una reproducción de la función de validación con Python 3.13.5, normal y `-O`; esto **no sustituye** los 52 casos reales ni certifica un build.

## Siguiente trabajo verificable (Work)

### A. Gate host; obligatorio antes de usar insumos privados

Desde la raíz del checkout íntegro del PR #17:

```sh
python3.11 -B tools/native_compatibility/run_p04c_host_gate.py
python3.11 -B -O tools/native_compatibility/run_p04c_host_gate.py
```

Exigir **P04C_HOST_PASS** dos veces, 52 o más tests por ejecución, 0 errores, 0 fallos y 0 omitidos. Si un gate falla, corregir sin alterar pins aprobados y repetir. No convertir una prueba sintética en evidencia de Android.

### B. Recuperación de materiales originales de Work

Con el ZIP privado exacto autorizado, sin subirlo al PR:

```sh
python3.11 tools/native_compatibility/stage_recovered_inputs.py \
  --bundle /private/source/FlexyGram-P04c-Recovered-Original-Inputs.zip --verify-only
python3.11 tools/native_compatibility/stage_recovered_inputs.py \
  --bundle /private/source/FlexyGram-P04c-Recovered-Original-Inputs.zip \
  --output /private/work/p04c-original-inputs
```

Requiere estado `VERIFIED_ORIGINAL_INPUTS_ONLY`. Usar directorio nuevo y almacenamiento privado recuperable.

### C. Reproducir el experimento en máquina con NDK27 y CMake fijados

```sh
python3.11 tools/native_compatibility/reproduce_locked_16k.py \
  --sources /private/work/p04c-original-inputs/sources \
  --wheelhouse /private/work/p04c-original-inputs/original-wheels \
  --ndk /private/sdk/ndk/27.2.12479018 \
  --cmake /private/cmake/3.31.6/bin/cmake \
  --output /private/work/p04c-preflight-new --verify-inputs-only
python3.11 tools/native_compatibility/reproduce_locked_16k.py \
  --sources /private/work/p04c-original-inputs/sources \
  --wheelhouse /private/work/p04c-original-inputs/original-wheels \
  --ndk /private/sdk/ndk/27.2.12479018 \
  --cmake /private/cmake/3.31.6/bin/cmake \
  --output /private/work/p04c-rebuild-new
```

Se requiere el resultado `REPRODUCIBLE_STATIC_OUTPUTS_ONLY` y coincidencia de los **4 ELF, 3 wheels reconstruidos, 18 del overlay y A/B por SHA-256** con las evidencias revisadas. Guardar recibo/logs/artefactos en custodia privada. La primera invocación es solo verificación de inputs y **no** crea el directorio `p04c-preflight-new`.

### D. Lo que todavía requiere Work o laboratorio

- Compilar desde worktree aislado el APK experimental de Diagnostic con Chaquopy/JNI, sin tocar dependencias activas. Reauditar 96/96 ELF ARM64 para 4/16 KB y políticas de Diagnostic, incluidos manifest, imports y hashes. No utilizar una APK antigua como sustituto.
- Resolver custodia segura y recuperable de clave exclusiva Diagnostic; **generación no ejecutada**. Cualquier firma de APK requiere aprobación separada. Nunca publicar claves o contraseñas.
- Preparar dos perfiles Android ARM64 aislados, API24/4KB y API35+/16KB real, y ejecutar 12 casos en cada perfil junto con instalación, arranque, JNI/Python, logs y tráfico. Sin dispositivos/cuentas personales.
- No marcar `android_runtime_validated` true por pasar pruebas host, A/B, scanner ELF o zipalign.

**Límites obligatorios:** no fusionar PR #17; no comenzar Paso 4; no activar Actions, Production, autenticación ni proveedores externos; no publicar/distribuir APK. Devolver evidencias concretas de cada etapa, o estado BLOCKED con causa técnica y ningún falso PASS.
