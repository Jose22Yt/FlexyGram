# FlexyGram — Auditoría independiente de identidad y recursos

Rama auxiliar: feature/flexygram-identity-resources. Esta contribución solo añade pruebas y documentación; no edita recursos, manifiestos, Java, Gradle, JNI, Python ni autenticación. PR en borrador hacia develop, sin fusión automática.

## Hallazgos de la lectura de develop, 2026-10-19

| Área | Ruta | Observación |
| --- | --- | --- |
| Etiqueta Diagnostic | TMessagesProj/src/diagnostic/AndroidManifest.xml | Ya indica FlexyGram Diagnostic; conservar |
| IDs de flavors | gradle/variant-policy.json | Diagnostic y .app independientes; producción bloqueada |
| AppName | TMessagesProj/src/main/res/values/strings.xml | Todavía dice exteraless |
| AppNameBeta | mismo archivo | Todavía dice Telegram Beta |
| Icono principal/launcher | manifiesto Diagnostic | Usa ic_launcher_exteraless y versión round |
| AccountManager | TMessagesProj/src/main/res/xml/auth.xml | @string/AppName y dos iconos Exteraless |
| Nombre Gradle | settings.gradle | rootProject.name sigue siendo exteraless |
| Alias del lanzador | org.telegram.messenger.ExteralessIcon | Identificador técnico interno: NO confundir con marca visible |

Estos hallazgos proceden de inspección de fuentes, no de una APK en ejecución. Falta ampliar la auditoría a localizaciones, notificaciones, accesos directos, splash y otros recursos; no se afirma cobertura total.

## Código y pruebas

- tests/identity_resources/audit.py: lector Python de solo lectura, stdlib, con JSON estable; inspecciona políticas, launcher, recursos visibles, strings base, AccountManager y nombre de Gradle.
- tests/identity_resources/test_audit.py: ocho pruebas ficticias y sin conexión sobre cambios de identidad, recursos inexistentes, launcher ausente, nombres heredados y modo estricto.
- ERROR: regresión estructural, --strict devuelve código 1. REVIEW: elemento heredado que requiere evaluación, pero no bloquea compilaciones ni modifica nada.
- Paquetes fuente org.telegram.*, app.exteraless.*, JNI y avisos GPL/créditos NO se clasifican como marca visible ni se renombran.

Ejecutar desde la raíz del checkout:

    python -m unittest discover -s tests/identity_resources -v
    python tests/identity_resources/audit.py --strict

Las ocho pruebas con fixtures se ejecutaron en un entorno local aislado con 0 fallos. No se ha ejecutado todavía la auditoría contra un checkout completo del repositorio; Work debe ejecutarla allí, conservar el JSON y comprobar la cobertura real. No hubo compilación, instalación ni APK.

## Próximo cambio propuesto, con revisión previa

1. Inspeccionar todos los consumidores de AppName/AppNameBeta, aliases, widgets, accesos directos y localizaciones.
2. Aprobar un icono FlexyGram propio con variantes adaptable, round y monocromático y licencias verificadas.
3. Cambiar solo los recursos visibles en un PR funcional separado, con pruebas AAPT2, manifiesto fusionado y Diagnostic.
4. Conservar créditos originales y responsabilidad de @Lukhou23. No modificar identificadores de código, JNI, sesiones ni componentes de autenticación.
5. Revalidar esta rama contra develop al terminar P0.4c; no mezclarla con cambios de compatibilidad nativa.

Objetivo: adelantar un inventario reproducible y pequeñas pruebas sin interferir con el trabajo principal de Work.
