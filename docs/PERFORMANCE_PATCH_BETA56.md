# Parche de rendimiento para beta 56 (1345)

Base de distribución: beta 55 (`217044b99`). Incluye el parche intermedio `647ded444` y las correcciones siguientes.

## Evidencia que orienta el parche

La captura de beta 55 aportada para esta revisión contiene unos 48 segundos de planificación de CPU, dos arranques fríos y actividad real de la app. En la superficie principal de la segunda ejecución, 221 de 2530 registros llevan `App Deadline Missed` (8,74 %). El primer fotograma de los dos arranques aparece a 1075 y 1096 ms. Hay una interacción de 139 ms con 128 ms de CPU en main y un layout de RecyclerView de 46 ms.

Las lecturas locales de historial alcanzan 13,37 ms en storageQueue; el procesamiento local alcanza 87,39 ms en stageQueue. Esos tiempos no son bloqueos del hilo principal. Las esperas de cola y de red no se han atribuido con precisión.

Las decodificaciones visibles en la interacción incluyen iconos de reenvío y controles del reproductor. La traza no contiene pilas Java suficientes para atribuir los 128 ms completos a esos iconos. Tampoco demuestra que todo `Buffer Stuffing` proceda del blur. No se publican trazas ni datos personales con el parche.

## Cambios implementados

1. **Layout de la lista.** `DialogsAdapter` conserva el diff nativo pero solo restaura la posición cuando cambian las identidades, posiciones o geometría relevante de las filas. Una actualización del espaciador final no reposiciona todas las filas. Esto evita solicitar un layout por restaurar un ancla que ya sigue en el mismo sitio; inserciones, eliminaciones y reordenamientos conservan el comportamiento anterior.
2. **Recursos durante gestos.** Después del primer fotograma, `LaunchActivity` solicita preparar 11 PNG originales usados por navegación y controles de conversación. Un único worker de baja prioridad usa la caché existente de `IconsResources`; no crea vistas, no modifica Theme ni comparte drawables teñidos. La solicitud se cancela al pausar/destruir la actividad. Si no está lista, se usa la carga normal sin retrasar la navegación. La caché se invalida al cambiar configuración; las tareas antiguas no publican estados obsoletos. La API limita cada lote a 32 iconos y su cola a una solicitud.
3. **Captura de superficies ocultas.** El controlador del dock expone su visibilidad real. `DialogsActivity` omite la región inferior del blur cuando ambas vistas del dock dejan de ser visibles. Una opacidad mayor que cero conserva la captura durante las transiciones. Se conserva la captura del campo de entrada cuando existe.
4. **Dependencias del arranque.** Leer `mainconfig` desde `getGlobalMainSettings` ya no construye por accidente todo el controlador de cuenta cero. Se conserva la misma instancia de SharedPreferences y el acceso rápido cuando el controlador ya está creado. Esto corrige una dependencia prematura: no se contabiliza como ahorro de toda la fase Locale ni se traslada a un worker la inicialización de controladores de UI.
5. **Atribución de los costes restantes.** Secciones Perfetto emparejadas con `finally` en `ChatActivity.onFragmentCreate`, `ChatActivity.createView` y `Theme.createChatResources`. Permiten separar construcción de conversación y recursos en la comparación posterior sin registrar identidades ni texto.

## Correcciones intermedias incluidas

- Liberar la carga de chats después de errores de red, con espera mínima por carpeta y protección frente a callbacks anteriores al logout.
- Recuperar el archivo del watchdog de plugins en la cola del motor.
- Reutilizar la captura del fondo de chats cuando su contenido está limpio; mantener actualizaciones durante scroll, cambios y transiciones.

## Verificación y límites

`tests/test_trace_update56.py` ejecuta métodos Java de producción y el `IconsResources` completo con dobles Android; el diff usa la implementación de DiffUtil del repositorio. Comprueba cambios reales de filas, espaciadores, visibilidad parcial, carga asíncrona, cancelación, cambios de configuración y drawables independientes. Las pruebas existentes de startup, transporte, IA y renderizado siguen formando parte de la batería completa.

El workflow `FlexyGram UI beta debug ARM64` compila beta 56 desde `codex/flexygram-update56`, ejecuta las pruebas y verifica firma y bibliotecas nativas antes de entregar una APK. El resultado concreto se debe consultar en la ejecución asociada al commit; este documento no presume que esa ejecución haya terminado correctamente.

La APK de ese workflow usa firma de prueba. No se ha publicado una actualización firmada con la clave de distribución.

**No se afirma que el jank sea cero ni que se hayan eliminado los picos de 139 o 46 ms.** Hace falta una comparación de beta 55 frente a beta 56 en el mismo dispositivo y recorrido. La captura original tiene instrumentación gráfica detallada, cuyo coste también forma parte del escenario medido. El parche reduce trabajo demostrado en código; su beneficio completo en latencia y fotogramas se verifica en Android.
