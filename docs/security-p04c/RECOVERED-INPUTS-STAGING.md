# FlexyGram P0.4c — recuperación privada y reconstrucción offline

**Este procedimiento es experimental y no constituye una beta.** Complementa el runner y las recetas ya aprobadas en PR #17. Los contratos/locks activos de Diagnostic, Production, firmas, cuentas y servicios permanecen sin cambios.

## 1. Qué se ha añadido y verificado

- `tools/native_compatibility/stage_recovered_inputs.py`: valida el ZIP **privado** de recuperación de Work contra SHA-256 `17325285036532db37a4ed09600f5a62a61056de6a2c59bec1d17da550ea0d82` y el inventario/hashes/tamaños individualmente fijados en `docs/security-p04c/evidence-lab-integration/recovery-bundle-manifest.json`. Exige los 18 wheels originales, archivos fuente y manifiestos exactos, rechazando extracciones fuera del directorio, miembros extra/duplicados, symlinks y cambios. Solo copia a un destino privado nuevo, sin descargar ni ejecutar componentes.
- `tools/native_compatibility/pinned_freetype.py`: acepta el checkout Git en el commit `86bc8a95056c97a810986434a3f268cbe67f2902` **o**, en su ausencia, el export TAR obtenido por Work con SHA-256 `fdf98f8fc19df83d2640d7b6e40c5195f4a56b280c38582b04a5e84efd30add3`. No fabrica commits ni acepta un checkout existente incompleto. El TAR es una fuente alternativa verificada, no una prueba Android.
- `rebuild_candidates.py` y `reproduce_locked_16k.py`: integran ese mecanismo de FreeType sin alterar el conjunto de versiones, los contratos ABI, los hashes de ELF y wheels o la reconstrucción A/B ya definida.

Nuevas pruebas sintéticas: 14 sobre el ZIP de recuperación y 8 sobre FreeType. Junto a las 15 del ejecutor existentes: **37/37 PASS con Python3.13.5 y 37/37 con -O** en el entorno local. Las regresiones originales 207 de Work no se atribuyen a una ejecución nueva. Falta repetir la suite con Python3.11 y el checkout completo, y comprobar la reconstrucción con binarios auténticos.

## 2. Uso con insumos privados autorizados

Mantener el archivo de recuperación y todos los resultados **fuera de GitHub**, del repositorio y del almacenamiento temporal que podría desaparecer. No colocar claves ni contraseñas dentro de este ZIP.

Verificar antes de copiar (solo lectura):

```sh
python3.11 tools/native_compatibility/stage_recovered_inputs.py \
  --bundle /private/source/FlexyGram-P04c-Recovered-Original-Inputs.zip \
  --verify-only
```

Extraer únicamente los insumos originales verificados a un destino **que aún no exista**:

```sh
python3.11 tools/native_compatibility/stage_recovered_inputs.py \
  --bundle /private/source/FlexyGram-P04c-Recovered-Original-Inputs.zip \
  --output /private/work/p04c-original-inputs
```

Directorio resultante: `/private/work/p04c-original-inputs/original-wheels` contiene los 18 wheels originales, `/private/work/p04c-original-inputs/sources` las cuatro fuentes TAR y el export TAR FreeType. Estos archivos **no** son los tres wheels reconstruidos ni la APK experimental.

El script protege la extracción, no crea un almacén durable: la custodia/retención privada del directorio final compete al operador.

## 3. Reproducción de bibliotecas y ruedas

Con NDK **27.2.12479018**, CMake **3.31.6**, Python **3.11** y las herramientas originales revisadas, comprobar requisitos sin iniciar builds:

```sh
python3.11 tools/native_compatibility/reproduce_locked_16k.py \
  --sources /private/work/p04c-original-inputs/sources \
  --wheelhouse /private/work/p04c-original-inputs/original-wheels \
  --ndk /private/sdk/ndk/27.2.12479018 \
  --cmake /private/cmake/3.31.6/bin/cmake \
  --output /private/work/p04c-rebuild-new \
  --verify-inputs-only
```

Una vez que estén todos los requisitos instalados, repetir **sin** `--verify-inputs-only`, conservando un destino de salida nuevo que todavía no exista. El ejecutor construye GNU ld2.42 y recompila dos veces en subdirectorios independientes `a`/`b`, compara los cuatro ELF y las tres wheels reconstruidas con sus huellas originales de PR17 y comprueba las 18 del overlay. Se detiene ante discrepancias.

Salida válida: `REPRODUCIBLE_STATIC_OUTPUTS_ONLY` en `reproduction-receipt.json`, con los hashes de archivos calculados; **no** significa que JNI/Chaquopy carguen ni que Android 16KB funcione.

**No usar** el APK baseline de la Biblioteca como sustituto del experimental revisado. Los outputs y el recibo deben guardarse en un repositorio privado de artefactos autorizado o soporte duradero verificado; GitHub PR17 contiene solo fuentes/recibos y no los binarios. Para firma con una nueva clave debe resolverse previamente la custodia segura, revisar contrato v2 y obtener la autorización de firma todavía pendiente.

## 4. Trabajo que queda para un entorno Android/Work

- Reejecutar con Python3.11 + NDK/SDK/Chaquopy y fuentes/pins reales, comprobar bytes idénticos frente al experimento anterior y conservar los tres wheels y los cuatro ELF privados.
- Compilar la APK experimental en un **worktree desechable**, auditar ELF96/96 y todo el manifiesto/políticas. No declarar equivalencia de APK a partir de una compilación sin medir su contenido.
- Resolver custodia recuperable de clave privada Diagnostic; **generación autorizada pero aún no realizada**. Firmar requiere aprobación separada. No utilizar claves de Production ni subir claves a proveedores no autorizados.
- Usar el runner Android existente de Work solo en laboratorio aislado ARM64 API24/4 KB y ARM64 páginas reales16KB; ejecutar los12 casos por perfil y revisar logs, hashes, JNI, Chaquopy y contadores.

No hay autorización para fusionar PR17, publicar APK, habilitar Actions/Production, iniciar sesión, utilizar cuentas personales ni comenzar el Paso 4.
