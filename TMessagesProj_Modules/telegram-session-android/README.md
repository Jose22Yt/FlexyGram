# FlexyGram: integración Android de sesiones, cerrada y sin registrar

Responsable: @Lukhou23. Preparado sobre PR #35, sin modificar fuentes, licencias ni atribuciones de Telegram/Exteraless.

`src/main/java` contiene contratos, diario de **metadatos**, adaptación al controlador LOCAL y propietario del flujo. `src/android/java` consume APIs Android y los controladores originales. `src/main/cpp` contiene exclusivamente dos métodos JNI de lectura. `integration/` conserva el fragmento CMake y su parche **sin aplicar**.

Este módulo no tiene registro en settings.gradle, sourceSets activos ni manifiesto. No está en la APK que compila Work 2. No proporciona un transporte real, almacén de claves, cuenta autenticada ni sustituto de LoginActivity.

La conexión suministrada de dominio TELEGRAM siempre deniega, incluso por llamada directa. LoginFlowOwner acepta solo puertos LOCAL_SIMULATION; sus implementaciones ficticias y LocalSink están únicamente en las pruebas. Los puertos son contratos de código revisado, no aislamiento frente a adaptadores maliciosos en el mismo proceso.

El diario guarda scope, revisión, ID aleatorio de operación y fase. No contiene teléfonos, mensajes, códigos, contraseñas, auth_key o material del LocalSink. Un COMPLETED es un recibo de simulación local, nunca una autorización Telegram. Los archivos originales tgnet.dat, preferencias y DB no se reescriben ni reinterpretan.

El executor del propietario debe ser un worker asíncrono revisado. El propietario serializa sus tareas y limpia copias pendientes; un booleano true de startLocal/verifyLocal significa **encolado**, no código enviado/verificado. Consultar snapshots y Failure. No usar Runnable::run en Android; se usa solo en tests host. Al destruir una vista, cerrar Binding; al terminar el flujo, cerrar owner; tras muerte de proceso restaurar solo el marcador, sin replay. Las escrituras de resultado incierto requieren revisión, no rollback ni retry.

Instrucciones y límites: [docs/session-android](../../docs/session-android/README.md).
