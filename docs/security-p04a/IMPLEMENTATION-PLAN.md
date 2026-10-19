# Plan de implementación verificable, sujeto a aprobación

No se inicia ninguna de estas modificaciones funcionales en P0.4a. El objetivo es conservar funciones, contratos y P0.1–P0.3g sin abrir servicios ajenos.

## Orden mínimo recomendado

1. **Aprobar decisiones de identidad y matriz.** Confirmar ID propuesto `.app`, nombre/iconos propios, titular y canal/firma; inventariar rutas y los callsites de denegación actuales. Acordar qué capacidades siguen opcionales. No pedir credenciales para revisar arquitectura.
2. **Una separación de variantes con configuración privada y firma.** Gradle/sourceSets/manifiestos/políticas Java-JNI por flavor, cuentas/providers/rutas/recursos aislados. Producción incompleta falla cerrada y no se distribuye. P0.1 y backup permanecen comunes. Configurar resolvers propios solo tras autorización, sin autenticación real en esa etapa. Pruebas positivas con transportes sintéticos detectan módulos que deniegan permanentemente; negativas confirman que Diagnostic no cambia.
3. **Resolver compatibilidad nativa en un cambio independiente, en paralelo lógico con identidad.** Fijar wheels/recetas; experimento API24/27 y cuatro bibliotecas16KB, sin actualizar toda la toolchain a la vez. No requiere cuentas ni servicios. Revisar resultados antes de cambiar plataformas/Python/NDK.
4. **Implementaciones operativas por servicio solo tras revisión posterior.** Autenticación propia primero en laboratorio autorizado, sin cuentas personales; push opcional y traducción autorizada con contratos preservados, sin dependencias heredadas. No exigir backend si la API oficial elegida cubre el contrato; tampoco dar por conservadas funciones mediante un stub. Permisos/componentes externos se habilitan individualmente. No se incluye actualizador en esta propuesta.
5. **Cierre de beta por evidencia real.** Completar pruebas Android, backups/restauración y4/16KB para el SHA candidato; revisar firmas/licencias/privacidad y autorizar distribución por separado. Una suite JVM o compilación no sustituye este bloqueo.

No crear etapas solo para cambiar nombres o repetir builds aprobados. Cada cambio funcional futuro sí exige su propio artefacto/evidencias; no reutilizar el APK de P0.3g como evidencia de producción.

## Archivos previstos (no modificados ahora)

| Grupo | Archivos actuales / nuevos propuestos | Riesgo y puerta de prueba |
|---|---|---|
| Variantes/identidad | build.gradle raíz, TMessagesProj/build.gradle, settings.gradle, gradle.properties; nuevos src/diagnostic y src/production | Config común sobreescribe flavor, fallback de módulos, applicationId/cert equivocado. Verificar cada variante y cada manifiesto fusionado |
| Política/credenciales | gradle/telegram-api.gradle, push-services.gradle; DiagnosticPolicy.java, BuildConfig; nuevo esquema privado sin valores | Par parcial, configuración desconocida o propiedad no acreditada: rechazar sin log de valores; Diagnostic ignora configuración propia y ajena |
| JNI | jni/tgnet/DiagnosticPolicy.h, CMakeLists y consumidores de guardas | Discrepancia con Java o caché entre variantes: generar y verificar separadamente, probar transporte falso positivo/negativo |
| Recursos y entradas | AndroidManifest, res/xml/auth.xml, sync_contacts.xml, backup/extraction rules, valores/locales, mipmaps/aliases | Pérdida de launcher, enlaces/cuentas compartidos, restauración; pruebas de instalación y permisos por API, conservación de opciones y créditos |
| Datos | BackupAgent.java, SettingsBackupPolicy.java, UserConfig/SharedConfig, rutas FileLoader/MessagesStorage/ApplicationLoader | No reabrir sesiones ni modificar formato/allowlist sin revisión. Fixtures de restauración antigua/nueva, entidad truncada y límites/descriptores, comparación de archivos/prefs antes/después |
| Traducción | TranslationServicesPolicy y adaptadores Google; módulo translation-compat-diagnostic, consumidores Microsoft/DeepL | Stub productivo accidental, API rota, doble clase o AAR heredado. Comparar firmas/catalogues, HTMLKeeper/TLRPC, cancelación/errores; inventario DEX/grafo y transporte sintético |
| Push | PushServicesPolicy, Firebase/UnifiedPush callbacks, Gradle e inicializadores fusionados | Callback directo, token de scope anterior o inicialización SDK antes de validar. Matriz sin config/parcial/ajena/propia sintética, token jamás en logs/backup |
| Compatibilidad | Toolchain/pip/runtime fuente, prebuilt afectados | Regresión API24, imports/plugins,16KB. Receta con hashes y ensayo completo separado antes de aceptar configuración |

## Pruebas exigidas a una futura implementación

- Mantener las **93 regresiones históricas** como referencia; extenderlas sin omisiones silenciosas ni debilitamiento de expectativas. Usar datos inventados, nunca servidores reales para probar claves heredadas.
- Matriz por variante y buildType: IDs/etiquetas/autoridades/accountType/signing, permisos/exportados, BuildConfig, guardas Java/JNI, grafo resuelto y DEX. Diagnostic: INTERNET ausente, ID0/hash vacío, autenticación/sockets/plugins/push/traducción denegados incluso por callback directo.
- Producción: sin fachada diagnóstica ni literales universales de denegación que rompan servicios autorizados; ninguna capacidad se activa por preferencia. Sin configuración propia no debe existir un build operativo accidental. Validar mediante implementaciones falsas aisladas que los contratos sí pueden funcionar bajo una autorización sintética, sin red real.
- Credenciales: fuente única, par inválido/faltante/ajeno, firma ausente, recursos de otro proyecto, scope mutado; ausencia de secretos en logs, excepciones, backups y empaquetados. Escáner de fuentes, APK/anidados, AAR/JAR, DEX, recursos y reportes. Distinguir API ID público, credencial cliente propia, secretos servidor prohibidos y marcadores legítimos de licencia; no prometer APK sin toda cadena que parezca clave.
- Preservar ajustes permitidos y formato, probar que preferencias/archivos/fixture-tokens no cambian al restaurar, también framework/OEM. Ningún test debe acceder o borrar datos de Exteraless real.
- Build completo ARM64 con JNI/Chaquopy sin SKIP por cada SHA funcional; staging no depurable equivalente para medir después, con misma identidad/política. Ejecutar laboratorio de [compatibilidad](ANDROID-COMPATIBILITY.md), sin publicar APK ni habilitar Actions para obtener pruebas.

## Bloqueos obligatorios antes de primera beta autenticable

Pendientes: aprobación del diseño y applicationId; recursos propios/licencias; aplicación Telegram propia autorizada y custodia privada; firma estable y recuperación; separación de políticas y módulos sin pérdida de contratos; rutas/cuentas/providers externos independientes; permisos/componentes productivos revisados; servicio(s) de traducción autorizado(s) operativos o cobertura explícitamente acordada; push propio solo si se decide activarlo; resolución API24/27 y wheels16KB; laboratorio ARM64/Android moderno; backup/restauración real; escaneo, evidencia ligada al SHA, política de privacidad y autorización de distribución. Push no es requisito para autenticar, y un backend no se presupone obligatorio.

Permanece el [bloqueo Android offline previo](../security-p03a/VALIDACION-ANDROID-PENDIENTE.md): instalación/arranque, ausencia de cierres/tráfico, permisos/componentes, aislamiento de cuentas/sesiones y16KB. El incidente Telegram original sigue sin causalidad demostrada por registros del servidor. La integración de P0.3g y este diseño no declaran la app lista para beta ni validada en ejecución.
