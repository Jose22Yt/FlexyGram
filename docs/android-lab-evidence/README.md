# FlexyGram 1.0 — contrato de evidencias del laboratorio Android

**PR auxiliar independiente de P0.4c y del preflight PR #20.** No modifica Android, JNI, Chaquopy, Gradle, wheels ni la APK. El objetivo es comprobar que un informe estructurado del laboratorio es *completo y coherente*, para evitar declarar éxitos con casos omitidos o binarios equivocados.

**No se ejecuta Android aquí.** El verificador solo procesa un archivo JSON local de un laboratorio futuro. Los valores JSON son autodeclarados y pueden ser incorrectos o fabricados: la salida satisfactoria **no certifica ejecución real**, procedencia de datos, carga JNI/Python ni compatibilidad de 16 KB. Los logs originales y sus huellas deben ser corroborados por revisión humana y por el procedimiento `ANDROID-LAB-16K.md` del PR #17.

## Fuentes inmovilizadas para este contrato

Referencia exacta: PR #17 HEAD `867e1178719ff0bda8d9b5381b17ecc3ae8391e5`.

- APK experimental interna, sin instalar: SHA-256 `17c32ab39e3ac88213241a6bd643637469a4a4d47311a920b357a2e7b3128230`.
- Certificado de laboratorio: SHA-256 `27ef63ae50546c0af28c0ac54ef66a0c00614934cda86c6bea42d9d2759e7b83`.
- Cuatro bibliotecas ELF reconstruidas: `libexslt.so`, `libfreetype.so`, `libxml2.so` y `libxslt.so`, hashes fijados en `tools/android_lab_evidence/check.py`.
- Doce nombres exactos de `test_*` derivados de `tests/native_compatibility/runtime_cases.py` en ese HEAD.

**Si cambia la APK, firma, bibliotecas o tests de Work, el contrato queda obsoleto y hay que revisar y aprobar nuevos valores**, no modificar silenciosamente los hashes para que la puerta pase.

## Campos de evidencia requeridos

JSON raíz con *exactamente* `schema` (entero 1), `apk_sha256`, `cert_sha256` y `profiles`. Este último debe contener exactamente los objetos `api24` y `16k`.

Cada perfil exige los campos siguientes (no admite otros):

| Campo | Condición para revisión |
| --- | --- |
| `api`, `abi`, `page_size_bytes` | `api24`: API exactamente 24, ARM64, 4096 bytes. `16k`: API 35 o superior, ARM64, 16384 bytes |
| `package`, `permission_internet` | `io.github.jose22yt.flexygram.diagnostic`; `false` |
| `startup`, `jni`, `chaquopy`, `python` | Cada estado exactamente `pass`, informado por instrumentación real |
| `native_loader_errors`, `fatal_exceptions`, `anrs`, `network_attempts` | Enteros 0, no cadenas ni booleanos |
| `libraries` | Diccionario con exactamente cuatro ELF/hashes iguales a los del APK experimental |
| `cases` | Diccionario con exactamente los 12 IDs de `runtime_cases.py`, cada resultado igual a `pass` |

**El productor de evidencia no existe aún**. Work debe implementar un runner `androidTest` o equivalente aislado, verificando que las bibliotecas cargadas pertenecen realmente a los wheels experimentales y recogiendo pruebas objetivas. No se deben rellenar valores `pass` manualmente para sustituir una ejecución.

## Reproducción del verificador (sin Android)

```sh
python3.11 -m unittest discover -s tests/android_lab_evidence -v
python3.11 -O -m unittest discover -s tests/android_lab_evidence -v
python3.11 -m py_compile tools/android_lab_evidence/check.py
```

En la implementación local aislada se ejecutaron **24 pruebas sintéticas con 0 fallos**, tanto en modo normal como con `-O`, además de `py_compile`. Falta repetirlas con Python 3.11 y el checkout completo en Work.

Cuando exista un informe real de un laboratorio autorizado:

```sh
python3.11 tools/android_lab_evidence/check.py --evidence /ruta/privada/lab-evidence.json
```

El script no abre sockets ni llama a ADB, no instala la APK, no captura logcat y no genera artefactos. Rechaza archivos symlink y mayores de 256 KiB, JSON con claves duplicadas y campos desconocidos. La salida solo contiene códigos de estado y conteos, sin rutas ni contenido del informe.

`BLOCKED` y exit1: información incompleta, contradicciones, errores, omisiones o fuente ilegible.

`CONSISTENT_SELF_REPORTED_EVIDENCE_REQUIRES_HUMAN_REVIEW` y exit0: **solo coherencia de las afirmaciones JSON, no una prueba de que ocurrieron**. El campo `runtime_certified` siempre permanece `false`.

## Pasos todavía pendientes

1. Repetir las pruebas del PR y revisar el contrato con Work.
2. Construir el ejecutor Android en un PR de laboratorio posterior, sin añadirlo a producción ni habilitar servicios.
3. Obtener entornos Android ARM64 API24/4 KB y 16 KB, verificar `PAGE_SIZE` de cada uno e inspeccionar los hashes/paths de las cuatro bibliotecas *cargadas*.
4. Ejecutar los 12 casos reales y analizar logcat privado; verificar instrumentación independiente y evidencias de ejecución.
5. Revisar los resultados con el propietario **antes** de certificar Android, sustituir dependencias activas, fusionar P0.4c o distribuir una beta.

No modificar `main`, `develop`, credenciales, seguridad, servicios externos, firmas de producción, Actions ni la rama de Work. No fusionar este PR sin aprobación.
