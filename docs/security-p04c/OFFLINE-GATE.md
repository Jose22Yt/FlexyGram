# P0.4c — puerta de validación offline que falla ante pruebas incompletas

Fecha: 19 de octubre de 2026. Repositorio Jose22Yt/FlexyGram, PR #17.

## Objetivo

Evitar informes **PASS** engañosos por omisiones, errores de importación, fallos esperados o ejecución de cero pruebas. No sustituye la compilación Android ni verifica dispositivos.

Desde el checkout exacto del PR, con Python 3.11 y pyelftools 0.33 adquirido de una fuente verificada:

```bash
python tests/native_compatibility/run_gate.py --output /ruta/privada/evidence/p04c-offline-gate.json
```

El script usa unittest discovery sobre todos los \`test_*.py\` de \`tests/native_compatibility\`, emite un JSON sin variables de entorno ni credenciales y retorna código 0 **solo** cuando se ejecuta al menos una prueba y no existen errores, fallos, omisiones ni fallos esperados.

## Evidencias de esta continuación

- Se añadieron seis tests de la propia puerta: caso válido, skip, fallo, error de importación, expectedFailure y cero tests.
- \`python -m unittest -v test_gate_runner\`: **6/6 aprobadas** en Python 3.13.5 aislado.
- \`python -O -m unittest -q test_gate_runner\`: **6/6 aprobadas**.
- Ejecución limitada con las suites locales \`test_lock_contract\`, \`test_wheelhouse_hardening\` y el test de puerta: **24 casos ejecutados; 23 aprobados, 1 omitido; status BLOCKED y código 1**. Es la respuesta correcta porque el entorno no contiene un checkout Git completo. El test nativo con pyelftools NO se ejecutó en este ejemplo.
- No hay evidencias nuevas de APK, NDK, compilación Gradle, carga JNI/Python, compatibilidad API24 ni páginas de 16 KB.

## Requisitos antes de aprobar P0.4c

1. Ejecutar gate con **cero omitidos** en checkout íntegro del commit verificado, con las dependencias de prueba resueltas por hashes. Conservar JSON y log exactos.
2. Ejecutar las pruebas históricas de seguridad, traducción y variantes, sin trasladar el resultado histórico de 102 casos a un commit distinto.
3. Recompilar \`:TMessagesProj:assembleDiagnosticDebug\` ARM64 sin SKIP, contrastar APK y firma propia de laboratorio, XML/manifiesto, política Java/JNI y bloqueo real de producción.
4. Auditar el APK exacto por API24 y ELF, incluido contenido Chaquopy anidado; afrontar los cuatro ELF de 4 KB y riesgos GNU_RELRO, sin declarar compatibilidad 16 KB únicamente por pruebas estáticas.
5. Probar instalación y arranque Android en entornos apropiados de 4 KB y 16 KB, sin credenciales personales y sin afectar la app Exteraless instalada.

Mantener el PR #17 **en borrador** y no fusionarlo a develop sin autorización. No activar Actions, modificar main ni iniciar Paso 4.
