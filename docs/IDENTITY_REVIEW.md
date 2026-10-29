# Revisión de identidad — 29 de octubre de 2026

## Base y límites

Base de trabajo: `feat/signature-interaction-navigation-2`, `258dd3590f40ca0083a4b7bad6b413433c4e2c14`, candidato Alpha 1286. Se inspeccionaron metadatos y estado de PR #128, #129 y #130 y las ramas remotas. Los tres permanecen draft/unmerged. El PR de identidad se apila sobre #130, sin integrarlo en main ni dar por aceptado su contenido. No se incorporan cambios funcionales de ramas hermanas.

## Auditoría y limpieza

Se revisaron Gradle, manifest, XML de cuentas/contactos/shortcuts, overlays, consumidores Java de identificadores, firma, scripts Alpha, triggers de Actions y documentación principal. No se realiza sustitución global de namespaces en Java/Kotlin/C++: JNI y nombres internos permanecen iguales. No se borran herramientas de pruebas, parches de restauración, contratos históricos ni licencias. La limpieza consiste en reemplazar el README obsoleto y organizar las instrucciones vigentes; los informes antiguos siguen como evidencia histórica, no instrucciones Beta.

Los iconos Beta son copias exactas del overlay aprobado de Alpha. La única adaptación Java conserva el estilo predeterminado de burbujas para ambas identidades con el flag existente. No se alteran preferencias ni renderizado. Los verifiers Alpha continúan restringidos a Alpha; sus comprobaciones de fuentes ahora resuelven la variante explícita y sus XML de overlay.

## CI

La rama de misión no coincide con ramas de push que construyen o publican. El PR usa un job Python específico; los jobs generales de Android se excluyen únicamente para esta rama. No se desactiva globalmente un workflow. Las rutas de los otros workflows de PR se revisaron y no seleccionan los archivos funcionales cambiados. No se despacha workflow de entrega. Los workflows heredados no se convierten en publicadores Beta.

## Validación y pendientes

El comprobador `tools/identity/check_identity.py` valida las dos identidades, XML y recursos superpuestos, referencias relativas de documentos, coherencia de firma y preservación de componentes respecto al SHA base. La verificación se limita a fuentes; no sustituye AGP, manifest merge ni Android.

Quedan pendientes: clave oficial bajo custodia y huella pública; configuración Firebase/OAuth/Maps del propietario; aceptación del candidato base; configuración y ejecución autorizada de entrega Beta privada; Gradle real, JNI/Chaquopy ARM64, firma y payload; instalación independiente, login, contactos, notificaciones, compartir, enlaces, coexistencia y actualización en teléfono físico. No se ejecuta compilación, empaquetado, firma ni publicación Android durante esta misión.

El gate específico y el parseo de todos los workflows YAML pasaron localmente. Se conserva un manifiesto de hashes separado (`tools/identity/review.json`) y una capa reversible que permite a los contratos históricos recuperar exactamente sus fuentes originales sin modificar sus manifiestos. Se comprueba también el rechazo de bytes desconocidos.

El intento ampliado de suites históricas encontró errores/fallos y accesos a blobs históricos pendientes en el clon parcial; no se declara superado. Los checks completos de Alpha y las suites históricas deben repetirse en un checkout completo antes de la futura entrega. No se ejecutó Gradle para compensar esa limitación.

Resultados adicionales: paridad de fuentes `check_source.py` aprobada (11 componentes idénticos y proyecciones revisadas); 8/8 pruebas `test_interaction1286.py` aprobadas. En `test_signature1271.py`, 5 pruebas pasan y la comparación histórica restante necesita el blob de ComposerStyle del SHA `0e359f0e…`, no disponible localmente. Las plantillas de incidencias se actualizan para pedir versión/variante y evidencia sin datos privados.

Tras recuperar el submódulo multimedia fijado, la suite general `pytest tests/` terminó con **144 aprobadas y 31 omitidas** (corpus externo de plugins/informe R8 no disponibles). No se modifica el puntero del submódulo. El parseo YAML y `git diff --check` también pasan. Esto no convierte la suite histórica de Connected Alpha en completa ni acredita ejecución Android.

La misión adicional de custodia se documenta en [SIGNING_CUSTODY_REVIEW.md](SIGNING_CUSTODY_REVIEW.md). Se preparan generación y recuperación locales; no se genera ni entrega una clave definitiva en el entorno temporal.

La alternativa local automatizada de custodia y sus límites están en tools/signing/README_LOCAL.md; no se ha generado la clave definitiva en esta sesión.
