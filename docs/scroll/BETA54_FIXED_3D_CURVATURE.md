# Beta 54: aro 3D fijo y curvatura configurable

Versión `1.0.0-beta.54`, build `1343`.

El único efecto disponible es una proyección cilíndrica fija. Cada fila obtiene su
inclinación, posición vertical y escala horizontal de su posición en el área visible
y de la curvatura elegida. La forma permanece al detenerse y al tocar. Desaparecen
la envolvente temporal, la modulación por velocidad, los resortes y la retirada al tocar.

## Ajustes y compatibilidad

- Pantalla principal → Efecto 3D fijo.
- Dos interruptores independientes: lista de chats y conversaciones.
- Curvatura compartida de 0 a 100 %; 0 deja el dibujo plano, 100 alcanza 65° en
  los extremos. Valor inicial 60 %, equivalente a 39°.
- El deslizador previsualiza en memoria y persiste al soltar. Teclado,
  accesibilidad y separación de la vista durante un arrastre también guardan el valor.
- Las selecciones anteriores 1–3 se interpretan como el único 3D. Una lista
  desactivada sigue desactivada. No se reescriben preferencias durante el dibujo.
- Sin una curvatura guardada, la intensidad antigua aporta 35, 60 u 80 %.
  FlexyStudio exporta/importa la nueva curvatura y conserva las claves antiguas.

## Dibujo, interacción y coste

El scroll continúa a cargo del RecyclerView nativo. El efecto no registra un
listener de desplazamiento ni programa frames propios, y no lee preferencias en
cada fila. Un cambio de ajuste invalida las vistas observadas mediante referencias
débiles. Se reutilizan matrices, cámara y límites, con cachés limitadas a 64
proyecciones por frame y 32 grupos de mensajes.

Los álbumes y las capas diferidas de nombres, horas, reacciones y fondos comparten
su proyección. Los selectores reciben la matriz antes de sus transformaciones
nativas. Las filas móviles y las pasadas manuales de soporte de la pantalla
principal también se proyectan sin aplanar toda la lista durante las transiciones.
Solo una fila/grupo que pertenece a un menú o vídeo nativo externo utiliza su plano
nativo mientras ese elemento está presente; el resto conserva el aro. Un contenedor
de vídeo ya separado no excluye ninguna fila.

El toque inicial usa la matriz inversa de la forma mostrada. Se conserva un
desplazamiento constante durante todo el gesto para respetar distancias, velocidad,
pulsación prolongada y deslizamientos nativos. El mismo DOWN detiene la inercia
antes de llegar al manejador nativo, permitiendo abrir un chat o pulsar una burbuja
sin un primer toque dedicado únicamente a frenar. No se aplana la forma al tocar.

Los mensajes muy altos usan una transición gradual del pivote y una distancia de
cámara que mantiene su superficie delante del plano de cámara incluso con la
curvatura máxima. La exploración táctil de accesibilidad conserva los límites
nativos sin proyección. Desactivar las animaciones del sistema no elimina esta
geometría estática.

## Regreso desde segundo plano

Se encontró que `DialogsAdapter` solo permitía calcular diferencias grandes fuera
del hilo de interfaz en `DEBUG_PRIVATE_VERSION`. La versión oficial comparaba
listas grandes de forma síncrona, coincidiendo al volver con el resto del trabajo
de reanudación. Ahora, si la lista anterior o nueva tiene 50 filas o más, DiffUtil
se ejecuta en la cola de búsqueda; las listas pequeñas mantienen el camino directo.

Las claves de comparación se congelan en el hilo de interfaz como primitivas y
strings. El worker no consulta modelos de Telegram que puedan cambiar mientras
calcula. Una generación por operación evita que un resultado anterior reemplace
una recarga completa o una nueva operación. Las peticiones recibidas durante un
cálculo se agrupan en una siguiente actualización con el último callback de
posición. Guardado de posición, publicación de filas y notificaciones del adapter
se ejecutan en la interfaz. Una excepción al calcular vuelve a la recarga nativa
actual, y una excepción del callback de posición libera el estado ocupado.

La visita a páginas visibles en `DialogsActivity.onResume()` se realiza una sola
vez: el método común ya recorre todas las páginas y la lista de búsqueda. El
regreso desde un chat conserva su actualización específica. La reconexión nativa
de `LaunchActivity` comienza antes de ordenar diálogos y reanudar fragments,
conservando la actualización de su indicador en el punto original.

Estos cambios reducen trabajo bloqueante identificable al volver a una actividad
conservada. No cambian la sincronización, el bloqueo por código ni la restauración
necesaria cuando Android ha eliminado el proceso. El tiempo real de regreso
requiere medición en el dispositivo donde aparece el problema.

## Validación y compilación

Las pruebas ejecutan geometría, persistencia/migración, previsualización del
deslizador, estabilidad en reposo, inversa del toque, interrupción de la inercia,
límites de caché, álbumes y excepciones de overlays. Comprueban la ausencia del
motor temporal y las pasadas manuales de dibujo. El módulo también se comprueba
contra las clases reales del SDK Android 35, sin empaquetar una APK local.
Las dobles de prueba de matriz/cámara permiten verificar matemáticas y contratos;
no sustituyen una medición de FPS o latencia en un teléfono.

Las regresiones de segundo plano ejecutan los métodos del adapter con el DiffUtil
real del repositorio y una cola worker real controlada. Cubren listas de 1.000–1.200
filas, publicaciones solo en UI, resultados fuera de orden, recarga completa
durante el cálculo, múltiples peticiones pendientes, modelos mutables, callbacks
reentrantes y excepciones al guardar posición.

Resultado local: **423 pruebas aprobadas y 39 omitidas**, sin fallos. Sintaxis
Java comprobada en los 10 archivos modificados/nuevos. Ejecución reproducible
con JDK 21, pytest y `FLEXY_SCROLL_ANDROID_JAR` apuntando al SDK Android 35:

```bash
python -m pytest tests -q -p no:cacheprovider
```

La APK se solicita mediante `.github/workflows/ui-beta-debug.yml` en la rama
oficial después de los tests y del push. Por petición del propietario, no se
supervisa el progreso ni el resultado del workflow.
