# Beta 46 — menos trabajo en el inicio

11 de noviembre de 2026 (America/Bogota). Fuente `1.0.0-beta.46`, build `1335`; sin compilar una APK.

La espera en el icono del sistema depende de que la aplicación termine de preparar su primera interfaz. `StartupSplash` ya retiraba la ventana nativa cuando Android permite mostrar contenido, sin esperar la red ni mantener un temporizador. Esta revisión conserva esa política y reduce trabajo del arranque.

## Cambios

1. **Almacenamiento de plugins en su worker.** `PluginsController.init()` abría y migraba los permisos mediante escrituras síncronas y creaba la carpeta de plugins antes de comprobar si el motor estaba habilitado. Ahora esas operaciones pertenecen al executor de `PythonPluginsEngine`, antes de iniciar Python e importar el cargador. Los permisos se siguen verificando antes de ejecutar plugins. Si falla la preparación, el intérprete no empieza y las solicitudes reciben el resultado de error. Las solicitudes que ya estaban en cola comprueban el resultado del primer inicio antes de repetir trabajo.
2. **Preferencias de bots web bajo demanda.** Se elimina su apertura anticipada en `ApplicationLoader`. El acceso público usa una instancia sincronizada/volatile. La limpieza de una cuenta abre las preferencias aunque nadie las haya utilizado en el proceso actual, para no dejar registros persistidos de una sesión anterior. No se borran los registros de otras cuentas.
3. **Recursos de texto reutilizados.** `Theme.createCommonMessageResources()` recreaba seis `TextPaint` y un array de proporciones en cada llamada. Los objetos se crean una vez y sus tamaños se vuelven a aplicar cuando corresponde. La prueba ejecuta mil reinicializaciones sin crear más pinturas y comprueba que los cambios de fuente/densidad siguen aplicándose.
4. **Diagnóstico explícito.** La beta de depuración iniciaba LeakDetector y su barrido por segundo, que puede pedir `System.gc()`, registraba fragmentos/hojas y arrancaba el detector ANR y una política VM. Ahora esas tareas requieren `-PdebugTools=true`, indicador que el proyecto ya tenía. Se conservan los mecanismos de protección de plugins y la política de informes de errores existente. La APK de depuración seguirá siendo de depuración: no se afirma equivalencia general con una compilación release.
5. **Glyph fuera del recorrido anterior a la interfaz.** En un arranque UI, el enlace con el servicio Nothing se ejecuta en el callback de servicios que deja una oportunidad de renderizado. En entradas sin interfaz, o desde un hilo que no sea el principal, conserva su inicialización inmediata. No se mueven las vistas/controladores de chats a un worker ni se añade una pausa fija.
6. **Trazas por fase.** Se añaden `Flexy.startup.native_load`, `Flexy.startup.locale`, `Flexy.startup.configs` y `Flexy.startup.launch_resources`, con cierres `finally`. Complementan las secciones existentes de controladores, SQLite y servicios. Permiten localizar el tiempo pendiente mediante Perfetto/Systrace sin introducir pantallas de diagnóstico en el flujo del usuario.

Se conservan el orden de configuración, la restauración de FlexyStudio, los ajustes de bloqueo, la preparación de los diálogos locales de la cuenta seleccionada, la red y el registro de notificaciones. La pantalla principal permanece en su diseño por defecto; no se recupera el estilo iOS retirado en beta 45.

## Verificación

- **392 pruebas correctas, 39 omitidas** por corpus/herramientas ausentes en este entorno.
- Seis regresiones nuevas: identidad de pinturas y cambios de tamaño, apertura concurrente de preferencias y limpieza tras un inicio frío, solicitudes del intérprete en cola y errores de preparación, ausencia de migración anticipada con el motor apagado, diagnóstico optativo y secuencia Glyph UI/frontal frente a segundo plano.
- Las pruebas ejecutan los métodos reales con dobles explícitos de Android/servicios. Se conserva la batería anterior de orden de cuentas y servicios del arranque.
- `SharedPrefsHelper` comprobado de forma aislada con el jar real de Android API35. Sintaxis Java revisada. No es una compilación completa con API37.

```sh
python -m pytest tests/test_startup46_work.py tests/test_startup42_work.py tests/test_startup_splash.py -q
python -m pytest tests/ -q -p no:cacheprovider
```

## Medición pendiente en teléfono

No se ha medido un tiempo de apertura Android, TTID/TTFD, FPS o porcentaje de mejora en un teléfono durante esta revisión. Las cifras de objetos de las pruebas no son milisegundos de arranque.

Con la próxima APK hay que comparar aperturas frías y regresos desde segundo plano con la misma cuenta/datos, tipo de compilación y estado de diagnóstico. El registro `Displayed`/`am start -W` y una traza con las fases anteriores permiten separar la carga de bibliotecas, configuración, recursos y primer contenido. También deben revisarse enlaces externos, bloqueo con contraseña, cuentas secundarias y el motor de plugins habilitado/deshabilitado. No hace falta borrar los datos de la aplicación para realizar esa comparación.
