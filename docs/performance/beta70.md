# beta70: ciclo de vida y presupuesto de materiales

Base 545000ecdf5ac85fdf99d3d841c2d0c94d560c69; versión
1.0.0-beta.70-render-budget, código 1359. Mismo paquete de prueba nativa optimizada.

## Barra inferior principal

El usuario volvió a reportar que el material desaparece al salir y regresar, pese
al ajuste ON. Los cambios de beta68/beta69 no se consideran aceptación en su teléfono.

La fábrica y la actualización de colores de MainTabsActivity excluyen siempre el
shader Liquid Glass de Telegram. Un provider normal específico para esta barra
mantiene su alfa independiente del flag global. Otros consumidores de mainTabs y
los materiales nativos de conversación conservan sus políticas anteriores.

OFF no crea el host Compose. ON permite únicamente el material Kyant opcional,
con las restricciones existentes de API, hardware y ahorro de energía. Hasta estar
listo se conserva el fondo normal y los controles nativos; no aparece la lente de
Telegram como sustituto. La captura normal sigue actualizándose cuando Kyant no
está renderizando, incluso si la preferencia sigue ON y el dispositivo no lo permite.
No se cambian coordenadas, márgenes ópticos, medición ni acciones de las pestañas.

Al pausar el fragmento se libera la composición real y su fuente gráfica, se
cancelan callbacks y gestos pendientes y se devuelve la propiedad a los controles
nativos. Un indicador de host reanudado evita que callbacks de ventana la reactiven
mientras está pausada. Al regresar se relee la preferencia persistida y una única
comprobación pre-draw crea la composición después del layout. No se usa sondeo,
retraso fijo ni reloj continuo. La reactivación tras ahorro de energía también
programa esa comprobación. Esto aborda la retención de recursos de la composición;
no demuestra todavía la desaparición del síntoma en la GPU del teléfono del usuario.

La sincronización reutiliza un ArrayList pequeño y ordena por posición física en
el mismo buffer. Solo publica otra lista de pestañas cuando cambia su identidad u
orden. El escaneo de selección no crea listas intermedias.

## Interfaces superior e inferior de conversación

Los drawables nativos conservan display lists al cambiar de presentación. Antes,
la selección de regiones de blur incluía cualquier drawable con display list y
alfa positivo, aunque el estilo actual ya no dibujara esa pieza. Ahora un indicador
de participación excluye materiales inactivos sin alterar su alfa de transición.
La cabecera actualiza las piezas que utiliza; las islas del compositor excluyen
la banda completa cuando la sustituyen. Un dibujo real por hardware recupera la
participación automáticamente, incluidas rutas alternativas y transiciones.
Los snapshots por software no cambian la propiedad del material en pantalla.
Las actualizaciones repetidas del indicador no invalidan la fuente de nuevo.

Se mantienen el acento opcional del chat, las burbujas limpias, los ticks, la hora
pequeña y el selector de interruptor de beta69. El rebote global y las funciones
retiradas de la base nativa no regresan. No se cambia sincronización, SQLite ni
el protocolo de carga de chats.

## Verificación y límites

- Suite Python/JVM: 546 pruebas pasadas, 41 omitidas por dependencias opcionales.
- Harness Android/Compose: 7 pruebas pasadas; composición liberada al pausar y
  recreada al regresar, preferencia persistida, reutilización de listas y geometría
  LTR/RTL, resize y dispatch nativo.
- Prueba de regiones: banda e isla pasan de 2 regiones a 1 al excluir la banda;
  10000 asignaciones iguales producen una sola notificación por transición y
  conservan el alfa. No es una medición de FPS.
- Snapshot reforzado: 2 pruebas pasadas; 1000 capturas conservan la exclusión de
  la banda y el estado de las islas.

No se dispone de medición física de arranque, jank ni consumo en esta versión.
La compilación completa y la aceptación visual siguen pendientes de CI/APK y de
probar abrir/cerrar/reabrir, alternar el ajuste y el ahorro de energía en el teléfono.
