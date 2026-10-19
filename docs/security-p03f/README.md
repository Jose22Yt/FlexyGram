# P0.3f — fachada de compatibilidad Microsoft/DeepL

Proyecto FlexyGram 1.0, responsable @Lukhou23. Fase aislada; no sustitución de producción.

## Integración aprobada y alcance

PR #11 verificado con HEAD **8900fc8222f8f6ff3dd3a3c673a7bdd9ad9179d9**, base develop y 20 archivos exclusivamente bajo `docs/security-p03e/` y `tests/translation_dependency/`. Integración únicamente en develop: **3cd4177369b35c02963d29cfbc11e3993fcfc268**. Las evidencias históricas permanecen intactas.

Nueva rama: `security/paso-3-p03f-translation-compatibility`. No modifica producción, dependencia activa, manifiestos, política, navegación, diseño, rendimiento ni actualizador. Main permanece intacta. PR #2 permanece abierto. No se habilitan Actions, Internet, autenticación, Firebase, push o proveedores.

Módulo independiente: `tests/translation_dependency/facade/`, con settings propios y sin inclusión desde el proyecto Android. Es Java fuente, sin claves ni identidad de aplicación ajena. El namespace `app.nekogram.translator` se conserva deliberadamente como contrato binario. No implica atribuir a FlexyGram el código original. Se conservan licencia GPL-3.0 y créditos.

## Compatibilidad comprobada

| Contrato | Implementación y evidencia | Diferencia o límite |
|---|---|---|
| `BaseTranslator()` / `translate(String,String,String)` | Método final, `throws Exception`, conversión de entrada, invocación de implementación y nuevo Result con conversión inversa | No añade validación ni conmutación de proveedor al pipeline |
| `translateImpl(String,...)` y `translateImpl(String[],...)` protegidos | Subclases y prueba de array secuencial, sin conversión adicional y con interrupción al primer fallo | Sin proveedor real |
| `getTargetLanguages`, `supportLanguage`, `convertLanguageCode` | 134 Microsoft / 123 DeepL; orden íntegro del inventario P0.3e; pertenencia exacta; null/vacío/auto conservados por el contrato base | Lista inmutable; no promete capacidad real del servicio |
| Campo protegido Gson y helper protegido `a(String)` | Descriptores conservados; MD5 de compatibilidad probado con dato ficticio | Gson ya existente, no se introduce SDK; helper no es criptografía de seguridad |
| `Result.translation`, `Result.sourceLanguage` | Campos **public final String**; constructor de paquete, `of`, equals y hash XOR compatibles | `toString()` se redacta deliberadamente, no imprime texto ni idioma |
| Microsoft / DeepL | Constructores públicos sin argumentos, `getInstance`, métodos protegidos finales y listas con firmas originales | Instancias normales cerradas; constructores adicionales exclusivamente para transporte ficticio |
| `DeepLTranslator.setJwt(String)` | Símbolo conservado; rechaza siempre con código fijo, sin guardar argumento | No reproduce ni autoriza JWT heredados; consumidor actual no lo llama |
| `Http429Exception()` | Clase/subtipo IOException y constructor conservados | Diagnóstico fijo seguro; el transporte ficticio usa FacadeFailure con estado 429, no afirma paridad de errores HTTP reales |
| Códigos chinos | zh-CN→zh-Hans, zh-TW→zh-Hant; inversa en el resultado, sensibles a mayúsculas | Alias insensibles a mayúsculas pertenecen al consumidor RealMicrosoft, no al contrato base |
| Conversión del consumidor Microsoft | `auto`→null; aliases zh, zh-HK, zh-Hans y otros comprobados sobre el archivo Kotlin real | Empty permanece empty; DeepL no hereda automáticamente esa conversión |
| HTML, entidades y Unicode | Datos ficticios con emoji, combinantes, chino, árabe, entidades HTML, tags y saltos de línea; transporte opaco sin alterar contenido | No se traduce realmente ni se demuestra semántica HTML de un servicio |
| Cancelación | Antes, durante, excepción e interrupción; mensajes seguros; bandera de interrupción conservada; 0 o 1 llamada según caso | Cancelación cooperativa: no hay socket/HTTP que abortar; AAR no tiene token de cancelación equivalente en su firma |
| Errores/reintentos | 400/403/429/456/500/504 y estado inválido; IO/runtime/respuesta nula/inválida; causa privada descartada incluso si la excepción ya parece de fachada | Tipos del transporte nuevo no se declaran idénticos a los motores opacos; no hay reintentos ni fallback implícitos |

## Consumidores reales y compilación

`test_real_java_and_kotlin_consumers_compile_and_link` compila **archivos completos sin modificarlos**:

- `TMessagesProj/src/main/java/tw/nekomimi/nekogram/translate/source/RealMicrosoftTranslator.kt`.
- `TMessagesProj/src/main/java/tw/nekomimi/nekogram/translate/source/fallback/DeepLTranslatorNeko.java`.
- `TranslationServicesPolicy.java` real para la ejecución de denegación.

Dos compilaciones: una contra la fachada y otra contra el AAR original. Ambas se ejecutan con **solo la fachada en el classpath de traducción**, verificando enlace Java/Kotlin, campos públicos y denegación real de la política. No se inicializa ningún motor del AAR. Un harness adicional BaseTranslator/Result se compila una vez contra el AAR y se ejecuta por separado con cada artefacto, comparando resultados sintéticos.

Para alcanzar la ruta de formato Microsoft se ejecuta **otro subproceso exclusivamente de pruebas**, con un doble permisivo de la política y un adaptador Microsoft ficticio inyectado mediante reflexión en el valor lazy del objeto Kotlin. No se cambia la política ni el consumidor de producción. Se comprueba la ruta real de aliases, texto simple, codificación/decodificación y preprocess con siete destinos. HTMLKeeper, TLRPC y TranslateAlert2 son dobles: verifica el wiring del consumidor y la conservación del objeto entidad ficticio, **no los offsets ni el parser real**. DeepL wrapper enlaza también en este subproceso, pero su singleton por defecto continúa cerrado.

La reflexión sobre el lazy es test-only y depende del runtime Kotlin usado. No forma parte del JAR main ni de una arquitectura propuesta para producción.

## Resultados y entorno

**83 pruebas aprobadas, 0 fallos y 0 omisiones: 69 anteriores (26+27+4+12) y 14 nuevas.** Logs en `evidence/`. El control anterior de aislamiento solo añade `docs/security-p03f/` a su lista documental permitida; las nuevas fuentes siguen bajo `tests/translation_dependency/`, ya permitido. No se relajan los controles sobre producción o políticas. El nuevo control compara además producción y evidencia P0.3e con el commit de integración.

- JDK Temurin **21.0.12.1+1** para javac, Java y Gradle de laboratorio.
- Gradle **9.7.1**, ejecución offline `clean jar`: exit 0 / BUILD SUCCESSFUL. Solo el módulo Java aislado; no Gradle Android, AGP, JNI ni Chaquopy en esta fase.
- Kotlin compiler **2.4.0** y bibliotecas ya presentes en Gradle; consumidores con JVM target 1.8. No se actualiza Kotlin del proyecto.
- Gson **2.14.0**, JAR existente verificado; contrato protegido conservado. No se empaqueta una nueva copia en la aplicación.
- Android SDK **API24 revisión3**, instalado únicamente para este control; Build Tools **36.0.0** para D8. Compilación de **todas las fuentes main de la fachada contra el bootclasspath real android-24/android.jar**, source/target 8, seguida de D8 **--min-api 24**.
- Avisos javac: source/target 8 obsoletos para JDK21. No errores de API en este alcance. No se compila el código del módulo únicamente contra el JDK y se presenta como compatibilidad Android.

**Alcance Android preciso:** compila contra stubs API24 y produce DEX de la fachada. Gson se usa como classpath; sus dependencias no se reempaquetan. No prueba ART, emulador, clases Android en ejecución, toda la cadena Kotlin/OkHttp/Gson, red, TLS, minificación R8 ni el empaquetado de la aplicación completa. No genera una nueva APK, AAR de reemplazo ni ejecuta Android. No hay instalación, distribución, sesión o llamada a Telegram/Microsoft/DeepL.

Escaneos del JAR y DEX exclusivos de la fachada: completos y sin candidatos conocidos de claves, paquetes/certificados ajenos o configuración de servicio embebida. Scanner estático con sus límites habituales; no prueba ausencia universal de secretos. Se conserva también inventario/hash de fuentes.

### Reproducción

Configurar rutas locales verificadas, sin credenciales:

```sh
export PATH="$JDK21/bin:$PATH"
export GSON_JAR=/ruta/gson.jar
export KOTLIN_LIB=/ruta/gradle-9.7.1/lib
export TRANSLATOR_CLASSES_JAR=/ruta/clases-originales-verificadas/classes.jar
export ANDROID_SDK_ROOT=/ruta/sdk
export GRADLE_USER_HOME=/ruta/cache-gradle
export FACADE_EVIDENCE_DIR=docs/security-p03f/evidence
python3.11 -m unittest discover -s tests/security -v
python3.11 -m unittest discover -s tests/translation_safety -v
python3.11 -m unittest discover -s tests/translation_runtime -v
python3.11 -m unittest discover -s tests/translation_dependency -p test_prototype.py -v
python3.11 -m unittest discover -s tests/translation_dependency -p test_facade.py -v
GSON_JAR="$GSON_JAR" /ruta/gradle-9.7.1/bin/gradle --offline --no-daemon \
  -p tests/translation_dependency/facade clean jar
```

El SDK debe contener API24; la prueba falla si falta, sin sustituirla por el JDK ni omitirla. El AAR de referencia se valida mediante las pruebas P0.3e y no es un motor ejecutado por las pruebas de fachada.

## Pendientes antes de cualquier reemplazo

**Alta — No es seguro sustituir hoy la dependencia activa.** Hay compatibilidad de las firmas consumidas y viabilidad de una fachada fuente, no una implementación autorizada operativa de los servicios.

1. Seleccionar transporte autorizado con fuentes/licencia verificables y autorización revisada por proveedor. No reutilizar JWT, claves, endpoints privados ni identidad ajena. Auditar credenciales, registros, errores, cuotas y tratamiento de texto privado. No hay backend en esta fase.
2. Sustituir los constructores de inyección de laboratorio por una resolución de transporte autorizada e inmutable, revisada junto a la política. Los singletons de este prototipo permanecen cerrados; no son un proveedor utilizable.
3. Verificar funciones/formalidad y códigos contra contratos oficiales del transporte elegido; el inventario histórico no demuestra soporte vigente. El AAR DeepL no expone formality/tag handling en las firmas consumidas; la rama local con API propia es otro contrato y permanece intacta.
4. Medir cancelación end-to-end. **Hecho de código heredado:** RealMicrosoft captura `Exception` y llama `error(e.message...)`; puede convertir una CancellationException en IllegalStateException si algún día se abre la política. No ocurre con el guard actual y no se cambia en esta etapa. Un transporte nuevo seguro no resuelve por sí solo esa semántica del consumidor. El transporte bloqueante requerirá cancelación de trabajo real, sin fallback ni reintento tras cancelar.
5. Probar HTMLKeeper/TLRPC/preprocess reales, offsets UTF-16, entidades anidadas/solapadas, enlaces, código, texto largo y HTML malformado en Android. El passthrough y sus dobles no certifican paridad de formato.
6. Resolver el tercer consumidor del AAR, GoogleTranslatorNeko, sin eliminar funcionalidad ni clase silenciosamente: actualmente sigue enlazado al AAR y cerrado por política. Este módulo no implementa motores Google. Antes de retirar el AAR debe existir cierre completo de dependencias y contrato explícito de indisponibilidad/recuperación autorizada para Google.
7. Construcción Android completa con todos los consumidores, minSdk24, R8 y escaneo recursivo de la APK; cero duplicados de clases entre fachada y AAR. Probar ART API24 y dispositivo moderno, sin cuentas reales hasta la autorización correspondiente. Reproducir por separado la incidencia incremental Kotlin según el protocolo conservado P0.3e; no se cambian configuraciones para eludirla aquí.
8. Retirar verificablemente **ambas claves heredadas y la identidad ajena de la APK final**, conservando funciones Microsoft/DeepL y atribuciones. **El AAR activo permanece intacto y sus hallazgos siguen bloqueando cualquier beta distribuible.** El JAR limpio no limpia la aplicación ni acredita sustitución de producción.

Recomendación: revisar y aprobar esta fase como prueba de compatibilidad aislada. Autorizar una sustitución solo tras cerrar estos requisitos, revisar el diff funcional y reproducir compilación/escaneo y pruebas Android apropiadas. P0.4 y Paso4 no iniciados.
