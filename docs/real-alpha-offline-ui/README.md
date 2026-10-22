# Interfaz nativa de realAlpha sin conexión

Base fijada: PR #42, `57e3d958d161d77f3c468dcd9dc45644ccbc2fe7`.
FlexyGram, responsable @Lukhou23. Se conservan las cabeceras y la procedencia Telegram/Exteraless y sus licencias.

## Cambios implementados

- `DialogsActivity.onResume`: el bloque de permisos, notificaciones y ajustes OEM queda detrás del perfil cerrado; conserva el resto del ciclo de vida, observadores, navegación y redimensionamiento del teclado. También se guardan la entrada directa de permisos y sus resultados tardíos.
- Inicialización/paginación: no se disparan las cargas remotas de diálogos, historias, pistas, contactos y medios desde las rutas modificadas. No se modifica ningún estado de cuenta, `dialogsLoaded`, fin de diálogos ni estado de conexión.
- `DialogsAdapter`: la raíz offline entrega cero filas en lugar de filas auxiliares que esperan un fin de carga inalcanzable. La lista nativa recibe un `TextView` vacío, accesible y tematizado; se conserva su mecanismo de visibilidad y animación.
- Título: `DialogsActivity.setTitleOverlayText` sustituye únicamente la presentación del estado de red, con textos inglés/español y sin acción de proxy. `LaunchActivity` y su corrección biométrica permanecen intactas.
- Búsqueda: conserva el campo y las vistas originales; consulta únicamente `MessagesStorage.localSearch` en su cola original. No espera callbacks de búsqueda remota, mensajes o publicaciones. Un identificador descarta respuestas obsoletas; destruir la pantalla cancela la cola local y desacopla delegates. Los errores informan operación/tipo, nunca consulta o excepción completa. Los filtros de mensajes no añaden placeholders de un servicio deshabilitado (cuatro rutas de conteo/tipo/enlace coherentes).

Solo se activa con `flexygramOfflineDialogsUi=true`, conjuntamente con `flexygramRealAlpha=true`. Se rechaza StartupDiagnostic y se limita a realAlphaDebug sin reactivar variantes deshabilitadas. Sin la propiedad, fuentes/recursos y variantes existentes no cambian. El predicado en ejecución exige identidad realAlpha, aislamiento, credenciales vacías y seis capacidades cerradas; no lee preferencias ni intents.

## Integración para Work 2

1. Incorporar selectivamente el commit funcional de esta rama y el trabajo de #43, sin fusionar a main/develop. Las tres fuentes originales son idénticas en #42 y #43 al HEAD revisado `4cc8fd1cb87d646c8f196cecc2e86472923c590f`.
2. Materializar las copias verificadas (no aplicar el parche a `src/main/java`):

```sh
python3.11 tools/real_alpha_offline_ui/materialize.py
python3.11 tools/real_alpha_offline_ui/materialize.py --check
```

3. Preparar por separado la integración del login según #43 si se quiere combinar. Sus salidas `build/generated/flexygram-local-login` son distintas de las de esta corrección, ubicadas en `TMessagesProj/build/generated/flexygram-offline-dialogs-ui`.
4. En un entorno Android completo ejecutar, sin firmar ni instalar:

```sh
NATIVE_TARGET=arm64-v8a ./gradlew -PflexygramRealAlpha=true -PflexygramOfflineDialogsUi=true :TMessagesProj:assembleRealAlphaDebug
```

Para incluir también el login local, añadir `-PflexygramLocalLoginPages=true` después de su preparación. No usar `SKIP`. El materializador y Gradle rechazan fuentes originales, parche o copias modificadas: revisar y actualizar los hashes tras cualquier cambio real, sin desactivar los controles.

## Verificación y límites

```sh
# Configurar JAVA_HOME=JDK21, GRADLE_GROOVY_LIB=directorio lib de Gradle9.7.1,
# ANDROID24_JAR=android.jar de API24 y Python3.11 en PATH.
python3.11 -m unittest discover -s tests/real_alpha_offline_ui -v
python3.11 -O -m unittest discover -s tests/real_alpha_offline_ui -v
```

24 pruebas distintas; 48 ejecuciones finales aprobadas, cero fallos u omisiones. Los métodos insertados de búsqueda, cancelación y política se compilan/ejecutan con JDK21 y dobles locales; la guarda del adaptador se ejecuta aislada. Se comprueba además el cuerpo original de permisos/ciclo de vida, hashes, manipulación y generación idempotente. Las tres clases completas generadas se **parsean**, sin resolución de tipos. El método de vista vacía se compila contra SDK24 con colaboradores proyectados. El script Gradle se ejecuta con un **modelo DSL**, no con AGP. `-O` aplica a Python, no desactiva los asserts de los programas Java/Groovy.

No hay compilación Android completa ni APK de esta rama: faltan SDK37, BuildTools36, NDK27.2 y CMake3.31.6. No se repitieron los intentos bloqueados de Foojay. Tampoco hay prueba Android de temas, búsqueda SQLite/JNI, accesibilidad, gestos o disposición del texto. Verificar en el siguiente build autorizado: raíz vacía sin spinner, ausencia de diálogos de permisos/OEM, entrada/salida de búsqueda, temas, Atrás y recreación; después repetir con el login local combinado. No se afirma una mejora de rendimiento medida.

La búsqueda remota, mensajes y chats reales siguen indisponibles por las políticas offline existentes. No se habilitaron capacidades ni se borraron funciones del cliente original. Esta presentación es exclusivamente de laboratorio; retirarla para una futura variante conectada requiere revisión explícita.

Los logs finales y el recibo están en `evidence/`. La combinación con #43 se comprobó con `git merge-tree --write-tree`: sin conflictos textuales; eso no equivale a compilación o ejecución conjunta en Android.
