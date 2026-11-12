# Desplazamiento nativo sin efectos

Se retira el efecto de desplazamiento tanto de la pantalla principal como del
interior de las conversaciones. Esta revisión no cambia la versión de distribución
ni solicita una compilación de APK.

## Cambios

- Se eliminan el módulo `app.flexygram.scroll`, el editor de curvatura y sus textos.
- Las filas, álbumes, fondos, nombres, horas, reacciones y selectores vuelven al
  dibujo nativo, sin proyección 3D ni pasadas adicionales del efecto.
- Se elimina la conversión inversa del toque, sus eventos copiados y sus
  desplazamientos de coordenadas. Inercia, arrastre, pulsaciones y selección usan
  el recorrido nativo del RecyclerView.
- Se eliminan las matrices, cachés de grupos, observadores de preferencias y
  comprobaciones de overlays que solo existían para el efecto.
- Se conserva la organización compacta de ajustes de la rama oficial. Pantalla
  principal tiene seis apartados; desaparece Movimiento y desplazamiento.
- Los enlaces antiguos del efecto regresan al índice actual de Pantalla principal.
  Las claves antiguas de FlexyStudio siguen siendo aceptadas para no invalidar
  copias existentes. Ningún motor o pantalla las utiliza para activar efectos.

## Optimizaciones conservadas

Se mantienen la comparación de listas grandes fuera del hilo de interfaz, las
instantáneas inmutables, el descarte de resultados antiguos y la agrupación de
actualizaciones pendientes. También se conservan la visita única a páginas
visibles al reanudar, la reconexión adelantada y las optimizaciones previas de
renderizado, navegación y frecuencia de pantalla.

Retirar el efecto elimina su coste de CPU y de transformaciones por fila. El
desplazamiento sigue usando las optimizaciones nativas. Los tiempos de fotograma
y la fluidez percibida requieren comprobación en un dispositivo; no se afirma una
medición de FPS que no se haya realizado.

## Validación

- Suite general antes de integrar la última ampliación remota de ajustes:
  **414 aprobadas, 39 omitidas**, sin fallos.
- Regresión adicional del estado guardado del apartado eliminado: **1 aprobada**.
- Tras integrar la ampliación de ajustes compactos para todas las categorías:
  **42 pruebas de integración aprobadas** de ajustes, gestos y reanudación.
- Sintaxis Java verificada en los ocho archivos modificados que permanecen.
- Los tres XML de ajustes compactos se mantienen válidos.
- `ChatActivity` y `RecyclerListView` coinciden con sus recorridos nativos
  anteriores a la incorporación del efecto. En `DialogsActivity` se conserva la
  mejora de reanudación; `DialogsAdapter` y `LaunchActivity` permanecen intactos.
- No quedan llamadas o tipos del motor retirado en código, recursos o stubs.

Se guarda en la rama oficial con `[skip ci]`, sin solicitar ni supervisar ninguna
compilación de APK.
