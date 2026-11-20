# Validación de Native Test

La referencia es [beta.71 para ARM64][beta71] (`a5dd05506`, versión 1360). Ese
workflow verificó la APK de pruebas y registró 575 pruebas aprobadas y 39 omitidas.
El informe del APK indicó que esa versión todavía usaba perfiles de bibliotecas y
no incluía un perfil ART de FlexyGram generado en dispositivo.

## Rendimiento y perfil propio

Usar un Poco con HyperOS y un segundo teléfono de gama media. Comparar ambas
versiones en cada teléfono por separado, con la misma cuenta de laboratorio, estado
de caché, frecuencia de pantalla y condiciones de red y temperatura. Usar una
instalación existente y mantener los datos entre rondas. Registrar el identificador
de compilación, estado de Curvatura y modo de compilación de ART.

Para obtener capturas, seguir [el procedimiento del laboratorio](STARTUP_BETA61.md).
En `DeviceBenchmarks` pasar también `flexy.fixtureMessage` con un texto único
visible al abrir el chat sintético. Preparar suficientes chats y mensajes para
desplazar ambas listas. Los recorridos comprueban que las filas realmente se
muevan antes de registrar fotogramas.

Usar la misma APK de instrumentación para las dos versiones. Para medir beta.71
con las pruebas actuales, instalar la APK de beta.71 y la APK del módulo
`performance` por separado. Buscar el runner con
`adb shell pm list instrumentation` y ejecutar `adb shell am instrument -w`
con la clase `com.flexygram.performance.DeviceBenchmarks` y los argumentos del
laboratorio. `connectedDebugAndroidTest` instala el APK objetivo del árbol que
está compilando, por lo que podría sustituir la referencia.

1. Comparar beta.71 con la candidata con `flexy.compilation=none` en las dos.
   Registrar la mediana del primer fotograma y del contenido utilizable en frío y
   en caliente, la mediana de apertura con historial visible y el P95 del exceso
   sobre el tiempo disponible por fotograma en ambas listas.
2. Repetir los recorridos de scroll en la candidata con Curvatura activada y
   desactivada. Mantener el resto de los ajustes y conservar las trazas de AndroidX
   para localizar las esperas en el hilo principal, RenderThread o SQLite.
3. Ejecutar `ProfileGeneration` sobre el código candidato, comprobar el XML del
   dispositivo e importar los perfiles con el informe SHA-256 de la APK
   correspondiente. Reconstruir y usar `flexy.compilation=baseline` para evaluar
   el efecto del perfil. Confirmar en el dispositivo que ART lo aplicó.

```sh
python tools/startup_optimization/compare_benchmarks.py beta71.json candidata.json
python tools/startup_optimization/compare_benchmarks.py curvatura-off.json curvatura-on.json \
  --journey homeScroll --journey messageScroll
```

En el P95 de `frameOverrunMs` un valor positivo indica que esa parte de los
fotogramas se pasó del plazo. Comparar las diferencias con la variación entre
rondas y revisar las trazas antes de atribuir un cambio al código. El comparador
rechaza recorridos ausentes y capturas de modelos o builds de Android distintos.

## Fiabilidad y distribución

Usar una cuenta de laboratorio para estas comprobaciones y una segunda cuenta
para los casos de notificaciones. Registrar versión, dispositivo y resultado sin
incluir textos de mensajes, tokens ni datos de cuenta.

| Escenario | Resultado esperado |
| --- | --- |
| Actualizar sobre la APK anterior con la misma firma, con dos cuentas y un borrador | Las sesiones, ajustes y borrador siguen presentes. Android conserva el identificador y admite la actualización. |
| Abrir desde una notificación con el proceso detenido por el sistema | Se abre la cuenta y el chat correctos, aparece el historial y se conserva el contador de no leídos. Usar una terminación de proceso normal, ya que Android suspende notificaciones tras una detención forzada. |
| Llegada de push para una cuenta secundaria mientras se abre la principal | Se registra una sola notificación y se atribuye a la cuenta correcta. Repetir con la app en segundo plano y con la pantalla bloqueada. |
| Pasar de Wi-Fi a datos y recuperar la red tras modo avión | El cliente recupera los mensajes pendientes. Un mensaje saliente de laboratorio termina entregándose una sola vez y su estado se actualiza. |
| Abrir historiales y navegar tras recrear la actividad | El propio chat y su estado siguen siendo utilizables y responde la navegación atrás. |

Para probar el candidato con firma de distribución, verificar con `apksigner`
que el certificado coincida con el de la instalación de referencia antes de
usar `adb install -r`. La APK de Native Test usa su propio identificador y el
workflow oficial actual ensambla una revisión fijada distinta. La promoción del
candidato requiere pasar por la revisión y la aprobación de entorno ya
configuradas en [el workflow oficial](../../.github/workflows/beta-private.yml).

## Actualizaciones de la base

[La procedencia de los componentes][provenance] identifica el punto de partida
`2a308f49`. Contrasté ese punto con [exteraLess v13.1.1-beta15][upstream]. La
comparación mostró 152 commits posteriores y cambios en JNI de red,
`ApplicationLoader`, `MessagesController` y notificaciones.

- Se incorporó [`c0274f97`](https://github.com/exteraless/exteraless/commit/c0274f97bbb63f027bf585954dc6ee02883fa00b)
  en `CircularProgressDrawable` y `RadialProgressView`. El indicador M3
  recibe el tema que requiere aun cuando se crea desde una pantalla con otro tema.
- Ya estaban presentes los arreglos de `f6208a3d` para listas sin selector,
  `4288d935` para reacciones restauradas y `8a6537f2` para traducción tras
  reciclar una celda.

Revisar cada corrección relevante desde esa comparación en una rama separada.
Registrar SHA y archivos originales, dependencias que exige y prueba que protege
la integración. Aplicar primero correcciones aisladas y exigir los recorridos de
red, cuentas y push para cualquier cambio que toque esos componentes. Actualizar
la procedencia de los archivos importados junto al parche.

[beta71]: https://github.com/Jose22Yt/FlexyGram/actions/runs/44744196932
[provenance]: upstream-provenance.json
[upstream]: https://github.com/exteraless/exteraless/compare/2a308f49b41534a45198c35f5ed98079f102f057...v13.1.1-beta15
