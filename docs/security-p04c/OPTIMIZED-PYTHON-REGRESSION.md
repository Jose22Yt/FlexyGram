# P0.4c — verificación de pruebas con Python optimizado

Fecha: 2026-10-19. Alcance limitado a las pruebas aisladas de bloqueo de dependencias del PR #17. No autoriza integración a develop ni validación Android.

## Hallazgo reproducido

En el commit `f051142f99bc96c137406f7f102dfa8b4b3c56bd`, `test_lock_contract.py` utilizaba 16 instrucciones `assert` como controles de integridad de wheel locks. En Python con optimización `-O`, las instrucciones `assert` desaparecen. Ejecutar **`python -O -m unittest -v test_lock_contract`** sobre una copia exacta del archivo (SHA Git `495cb47f70b433d892e8eaf960829c0f539b8b1e`) produjo **7 fallos, 1 error, 1 omisión** entre los 10 tests. En consecuencia, no era válido depender del resultado del validador en modo optimizado.

## Corrección

Se sustituyeron las 16 comprobaciones por `require(condition, message)`, que llama explícitamente a `raise AssertionError` cuando no se cumple el contrato; no desaparece con `-O`. Se conservaron las reglas de versiones/hashes/ABI/hosts, los fixtures y los diez casos.

## Evidencias ejecutadas en el entorno local de esta revisión

Entorno Python 3.13.5 sin red ni checkout completo. Archivos de pruebas y wheelhouse equivalentes exactamente al HEAD de GitHub al comenzar la revisión.

- `python -m unittest -q test_wheelhouse_hardening test_lock_contract`: **18 pruebas; 17 correctas y 1 omitida; cero fallos**.
- `python -O -m unittest -q test_wheelhouse_hardening test_lock_contract`: **18 pruebas; 17 correctas y 1 omitida; cero fallos**.
- `python -m py_compile test_lock_contract.py`: **sin errores**.
- La prueba omitida es `test_real_repository_lock`, que necesita `TMessagesProj/python/wheels.lock.json` y `requirements.lock` en un checkout completo. No se cuenta como aprobada. La comparación de estos ficheros por conector GitHub ya se había hecho por separado en la revisión anterior.

## Gates restantes

1. Ejecutar `python3 -m unittest discover -s tests/native_compatibility -v` en el checkout del HEAD exacto del PR, con `pyelftools==0.33` obtenido y verificado por hash; **ningún test omitido**. Repetir al menos la suite de contrato con Python 3.11 y `-O`.
2. Ejecutar las 102 regresiones históricas (y nuevas pruebas) sin ignorar fallos, conservando logs reproducibles.
3. Construir `:TMessagesProj:assembleDiagnosticDebug` completo para ARM64 con JDK/Gradle/NDK/CMake/Chaquopy, verificar hash/firma/manifiesto y bloqueo de producción.
4. Auditar el ELF/APK real en API24, PT_LOAD/RELRO de 16 KB e imports de Python; verificar la carga y el arranque Android ARM64 (páginas 4 KB y 16 KB).
5. Mantener intactas las cuatro bibliotecas heredadas de 4 KB hasta resolverlas con binarios aprobados y evidencia. No usar pruebas sintéticas para certificar compatibilidad Android.

Este commit se limita a pruebas/documentación. `main`, `develop` y la rama original de Work deben permanecer intactas. PR #17 continúa en borrador.