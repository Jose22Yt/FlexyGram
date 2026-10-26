# Contribuir a FlexyGram

La dirección del proyecto corresponde a @Lukhou23; la cuenta propietaria es Jose22Yt. Abre una incidencia o un PR en este repositorio para discutir cambios. No se presupone un canal, dominio o cuenta adicional como oficial.

1. Parte de un HEAD integrado acordado y crea una rama independiente. `main` conserva actualmente un estado histórico; no es sinónimo del último código Connected Alpha.
2. Revisa los PR activos. Alpha1275 corresponde a Work1; no reemplaces sus cambios de cabecera, compositor, reproductor, burbujas, launcher, manifiesto o navegación.
3. Mantén PR en borrador hasta completar revisión y validación. No combines refactors, correcciones P0 y efectos visuales en un cambio difícil de aislar.
4. Conserva licencias, atribuciones y claves internas compatibles. No cambies applicationId, firmas, bases de datos, sesiones o claves de preferencias para corregir un nombre visible.
5. Adjunta pruebas y especifica su alcance: host, Android aislado, emulador o dispositivo. No publiques conversaciones, números, códigos, sesiones, trazas privadas o credenciales.
6. Usa las instrucciones actuales de [compilación](docs/BUILDING.md). Ningún secreto debe aparecer en un archivo versionado, issue, comentario o captura.

Antes de proponer código de aplicación ejecuta `python3 tools/connected_alpha/run_checks.py`, los controles de recursos y los ensayos pertinentes. Añade pruebas de comportamiento para cambios funcionales. Para esta rama de auditoría ejecuta también `python3 -m unittest discover -s tools/connected_alpha/prebeta -p 'test_*.py' -v`.

Las contribuciones deben contar con derechos compatibles con las licencias aplicables y conservar avisos existentes. Documenta la procedencia de nuevos recursos. Una captura sintética o una compilación correcta no certifican seguridad, cumplimiento integral de licencias o ausencia de regresiones físicas.
