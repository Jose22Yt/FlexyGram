# beta71: propiedad del renderizador del dock

Base 20cdf8f5ffbeec30ab4a049d4961407080bd8e21; versión
1.0.0-beta.71-dock-lifecycle, código 1360. Misma rama y paquete de la prueba nativa.

## Evidencia y alcance

El usuario sigue reportando el efecto ausente al cerrar y volver, con el ajuste
activo. No se considera aceptada la corrección anterior. El video adjunto dura
18,62 s: muestra el material antes de salir y el intento de reapertura; termina
antes de que la pantalla principal reaparezca. No aporta el estado interno del
renderizador ni permite identificar por sí solo la causa en ese dispositivo.
La versión instalada se ha solicitado, sin condicionar la reparación del defecto
reproducido en el código.

La prueba real de composición de una pausa sencilla también pasa sobre beta70.
Por tanto no se atribuye todo el problema a la preferencia ni se afirma que aquella
ruta sencilla reproduzca el teléfono. Las pruebas anteriores asignaban ready en
el host de ventana; esa asignación solo verificaba la política y no el retorno
real de una composición.

Se reproduce un defecto adicional ejecutando los métodos reales updateKyantDock,
clearViews y onPause en JVM con APIs de host explícitas: clearViews conservaba
kyantDockView. Ese objeto mantiene referencias finales a la barra y al viewPager
anteriores. Al reconstruir la pantalla, updateKyantDock veía el campo no nulo y
no añadía ningún renderizador a la nueva barra. El ajuste podía seguir ON mientras
el objeto retenido apuntaba a vistas antiguas. El test falla sobre beta70 con
«clearViews must drop the obsolete optical host» y pasa con esta corrección.
Esto demuestra un defecto de propiedad de vistas, no que todos los cierres del
teléfono recorran necesariamente esa misma ruta.

## Corrección

releaseKyantDock es la única ruta de liberación: borra primero la referencia del
fragmento, desacopla el host de la barra nativa, pausa/libera su composición y lo
retira del contenedor. Se usa al apagar el ajuste, pausar, limpiar/recrear vistas
y destruir el fragmento. La operación es idempotente.

Al regresar se construye una vista óptica nueva ligada a las vistas actuales.
No se intenta reciclar el contexto de composición ni las capas gráficas de la vista
anterior. Esto sustituye la retención del host de beta70; se conserva la comprobación
pre-draw existente. La preferencia persistente, la selección y la geometría nativas
no cambian. El modo OFF sigue sin crear Compose, y el flag global de Telegram sigue
excluido solo de esta barra. Se respeta la disponibilidad por API/HWA/ahorro.

La creación ocurre en el ciclo de entrada de esta superficie opcional, nunca en el
scroll ni en cada frame. 10000 actualizaciones con las mismas vistas reutilizan
el mismo host. No se reconstruyen chats, base de datos ni cachés por este cambio;
no se modifican shaders, magnificación, clipping ni sombras del material.

## Verificación

- Regresión JVM de propiedad de vistas: falla antes y pasa después; comprueba
  desconexión del dock/contenedor anteriores, vinculación al dock y escena nuevos,
  limpieza repetida, nueva vista al volver y ausencia de host al desactivar.
- Prueba Android/Compose adicional sin asignar ready: verifica publicación real
  de la composición, pausas y revelado tardío de la barra; después retira la vista
  óptica, detiene/reanuda la Activity y comprueba que otra vista realmente compone.
  Las APIs de MainTabsLayout/GlassTabView son hosts explícitos del harness y la
  capacidad de hardware es una entrada de prueba; no equivale a ejecutar la GPU
  física ni toda MainTabsActivity de producción.
- Suite Python/JVM: 547 pruebas pasadas y 41 omitidas en este entorno.
- Harness Android/Compose: 8 pruebas pasadas, sin fallos.
- Comprobación del diff: sin errores de formato.

Revisión final: aprobado para compilación; la aceptación física sigue pendiente.

La aceptación en el teléfono continúa pendiente de la nueva APK: mismo ajuste ON,
salir y volver, retorno desde otra pantalla, recreación y OFF/ON. No se prometen
FPS ni tiempos de arranque sin medición física. No se recuperan rebotes globales ni
las funciones retiradas de la base optimizada.
