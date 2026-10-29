# Contribuir a FlexyGram

Parte de la rama acordada para la tarea y registra su SHA exacto. El código reciente está en ramas de desarrollo; no supongas que `main` contiene el candidato actual. Crea una rama independiente y un PR con problema, cambio, pruebas y límites. No fusiones ni incorpores candidatos pendientes de aceptación de forma implícita.

Consulta [BUILDING.md](docs/BUILDING.md). Mantén los namespaces técnicos, claves de preferencias, compatibilidad nativa y avisos de licencia. Una migración de identidad no autoriza cambios de mensajería, navegación, renderizado o reproducción.

No añadas claves privadas, contraseñas, sesiones, números de teléfono, capturas personales ni configuraciones privadas de servicios. Usa `local.properties` o variables de entorno. No adjuntes APK públicas. Los reportes de errores deben incluir versión, dispositivo, pasos y registros depurados, sin datos de cuenta.

La comprobación de esta misión es `python3 tools/identity/check_identity.py` y `git diff --check`. No ejecutes Gradle, empaquetado, firma o pipelines de entrega sin autorización para la fase de compilación. Los informes deben distinguir comprobación de fuentes, compilación, pruebas aisladas y pruebas físicas. Las evidencias históricas y pruebas útiles se conservan.
