# FlexyGram — offline development foundation

Creado y dirigido por @Lukhou23. Rama `development/beta-offline-foundation`, derivada
del código revisado de PR17 en19200e843cc9bf31c27a99e7b6775494627b131e.
Preparación autorizada dentro del Paso3; **no es una beta operativa ni el Paso4**.

## Implementación

- Flavor opt-in `betaDevelopment`, solo Debug/ARM64, ID propio
  `io.github.jose22yt.flexygram.beta.development`. Sin firma ni credenciales.
- `gradle/beta-development.json/.gradle`: perfil independiente y validador real que
  rechaza capacidades externas, otra identidad, campos extra o aislamiento desactivado.
  Las políticas Diagnostic/Production originales y el contrato v1 no se modifican.
- JNI usa su propio scope SHA256:betaDevelopment. El nombre heredado de la macro
  `FLEXYGRAM_BUILD_DIAGNOSTIC=1` significa aislamiento del código común: se conservan
  las seis constantes false y las guardas nativas. No se convierte Production en beta.
- Manifiesto independiente de beta con las exclusiones offline revisadas, sin INTERNET,
  restauración, permisos sensibles o servicios externos activos; autoridades/datos
  derivan de su applicationId. No usa la firma del laboratorio.
- Fachada de traducción **en otro módulo**, `translation-compat-beta-offline`:
  contratos existentes conservados, sin transporte ni claves. Microsoft/DeepL y su código
  de cliente se conservan; esta variante no ejecuta proveedores remotos. El módulo
  Diagnostic nunca se incorpora al classpath beta. Una variante autenticable futura
  necesitará implementaciones/autorizaciones propias, no esta fachada cerrada.
- `BetaPreviewActivity` ofrece rutas sintéticas con los componentes reales `DialogCell`,
  `ThemePreviewMessagesCell`, `TextSettingsCell`, `ActionBarLayout` y Theme. Permite
  preparar navegación de conversaciones/ajustes y claro/oscuro sin crear cuentas,
  restaurar sesiones ni alterar las pantallas normales del cliente. Todo el código
  común sigue incluido; estos fixtures no prueban una conversación Telegram real.
- Inicialización **local** de JNI/Python bajo demanda, en executor fuera del hilo UI,
  importando solo `sys`, sin arrancar el motor de plugins. Maneja errores de enlace sin
  imprimir trazas, rutas, tokens o contenido privado; descarta actualizaciones tras cerrar.

## Estabilidad e interacciones

Se corrigió `ActionBarLayout.resumeDelayedFragmentAnimation`: si el callback programa
otro callback síncronamente, el final del método anterior ya no borra la referencia nueva.
La regresión ejecuta el método Java real, reproduce el fallo histórico y comprueba el arreglo.
No cambia curvas, duración ni diseño de las animaciones.

En las rutas beta, `LatestNavigation` conserva como máximo una petición y un frame,
coalesce pulsaciones mientras termina una transición y cancela lo pendiente en back,
pausa y destrucción. Una simulación Java real de1000 interacciones valida ownership,
última petición, reentrada y cierre. **No es una medición de FPS/lag en Android**.

Una regresión adicional del mismo harness reproduce cancelación síncrona durante la
consulta de transición ocupada: se comprueban de nuevo ownership/cierre tras esa consulta,
evitando ejecutar null o trabajo cancelado. Se conserva el registro rojo y las seis
pruebas finales pasan en ambos modos; no se cuentan subcasos como métodos adicionales.

## Construcción y comprobaciones

Perfil opt-in: `NATIVE_TARGET=arm64-v8a`,
`-PflexygramBetaDevelopment=true :TMessagesProj:assembleBetaDevelopmentDebug`.
Sin el flag no existe beta; con `SKIP`/otra ABI se rechaza. Release/Staging beta no
se habilitan. Production continúa con `FLEXYGRAM_PRODUCTION_INCOMPLETE`.

Requiere JDK21, Gradle9.7.1, SDK37/35, BuildTools36.0.0, NDK27.2.12479018,
CMake3.31.6, Python3.11 y submódulos en los commits fijados por el repositorio.
Para este experimento se reutiliza el overlay privado de18 wheels, incluidos los tres
experimentales. No se reconstruyen los cuatro ELF/tres wheels ni se promueven a los locks
activos. Se aplica la receta existente `tools/native_compatibility/prepare_experiment.py`
en checkout desechable, conservando los fuentes Java/JNI de esta rama idénticos.

Las seis pruebas de `tests/beta_development/` ejecutan Java/Groovy/CMake reales, sin
Android, y cotejan byte a byte las políticas protegidas con19200e8. Variables requeridas:
`JAVA_HOME`, `FLEXYGRAM_GRADLE_HOME` y `FLEXYGRAM_CMAKE`. Comandos:

```sh
python3.11 -B -m unittest discover -s tests/beta_development -v
python3.11 -B -O -m unittest discover -s tests/beta_development -v
```

El gate367 del PR17 fue ejecutado en19200e8, no se adjudica a esta rama funcional.
Su lista congelada de hashes no se modifica para permitir cambios nuevos de cliente:
esta rama requiere revisión propia, además de las pruebas de beta y la compilación.

## Límites

No se ejecutó Android. Faltan host ARM64 aislable, primer arranque, JNI/Python y12 casos
reales por perfil, medidas de interacción, restauración sintética y controles de tráfico.
Custodia recuperable y autorización independiente son necesarias antes de generar clave,
firmar o instalar. La APK Diagnostic29188186… y sus contratos permanecen intactos.
Una APK beta nueva necesitará su propio expediente/contrato, no repinar v1/v2 históricos.
Autenticación, servicios propios, firma de distribución y pruebas de cuenta vendrán
solamente con otra aprobación. No se habilitan Production ni GitHub Actions.

Resultados reales de compilación y bloqueos: [BUILD-RESULTS.md](BUILD-RESULTS.md).

Continuación Work2: [navegación, lifecycle y productor de eventos](CLIENT-NAVIGATION.md).

Siguiente preparación: [integración25 y recreación/diagnósticos del cliente](SECOND-BETA-PREPARATION.md).
