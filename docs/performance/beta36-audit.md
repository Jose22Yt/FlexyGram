# Auditoría de rendimiento — FlexyGram beta 36 / build 1325

Base revisada: `9a25bf5ae5ddecf47896ed040158fa3839ae68a1`, rama
`codex/flexygram-beta-glass`. Fecha: 10 de noviembre de 2026.

Esta revisión sigue las rutas de apertura desde DialogsActivity, capturas blur3,
materiales de cabecera/composer, navegación inferior, seguimiento de posiciones y
relleno/contornos de MessageDrawable. No constituye una certificación de todo el
código de Telegram, dependencias nativas, plugins o funcionamiento en dispositivos.

## Cambios y motivos

| Ruta | Problema observado en código | Cambio |
| --- | --- | --- |
| Apertura de chat desde la lista | ChatActivity.onFragmentCreate espera con CountDownLatch las lecturas de SQLite cuando falta el peer en memoria. La espera bloquea la interfaz. | ChatPeerPreloader resuelve primero el peer en la cola de almacenamiento de Telegram. Publica las entidades en el controlador de la misma cuenta y continúa la navegación en UI. El camino con caché permanece inmediato. |
| Navegación durante la precarga | Un resultado tardío podría abrir un chat tras otro toque, una pausa o la destrucción de la lista. | Número de generación y comprobaciones de propietario/cuenta antes de presentar el fragmento. Los fallos notifican un error sin volver a esperar almacenamiento en UI. |
| Contadores de barra inferior | saveLayer de toda la pestaña en cada dibujo para borrar con CLEAR el hueco del contador. | Clip diferencial de una silueta redondeada reutilizable, aplicado solo a los hijos. Después se dibuja el contador. Conserva la escala de aparición y el fondo/selector de la pestaña. |
| Programa Liquid Glass | Cada instancia releía el mismo recurso de texto. | Una copia inmutable de la fuente por proceso. RuntimeShader y sus uniformes siguen siendo exclusivos de cada instancia. |
| Superficies opacas | Se registraba la fuente y actualizaba el efecto aunque el resultado solo dibujase el color opaco. | Evitar ese registro cuando alfa es 255. Recuperar el camino completo al volver a transparencia. |
| Regiones de blur | El redondeo por resto de división no cubría correctamente coordenadas negativas y expandía una celda extra los límites ya alineados. | floor/ceil a la cuadrícula. |
| Caché de capturas | No incluía el origen de la región; el hash genérico de vistas solo incluía su identidad. | Incorporar límites, posición, escala, rotaciones, pivotes, tamaño, scroll, visibilidad y alfa. Rechazar reutilización cuando el contenido está sucio o tiene layout pendiente. Es una corrección de frescura visual; puede aumentar capturas donde antes se reutilizaba contenido obsoleto. |
| Composición de blur | Cambiar tamaño o quitar todas las regiones podía dejar la composición anterior si no había una captura nueva. | Comprobar también la composición sin capturas nuevas. Su hash existente evita volver a registrarla cuando no cambió. |
| Error al capturar | Una excepción podía dejar abierta la grabación y un hash marcado como vigente. | Cerrar la grabación en finally y aceptar el hash solo al completar la captura. |
| Posiciones entre ventanas | Una suscripción multiwindow creaba otro observador sin conservarlo para liberarlo. | Reutilizar un observador por vista, evitar registro adicional en el mismo árbol del ancla y liberar callbacks al limpiar/desuscribir. Las referencias a las vistas son débiles. |
| Relleno adaptativo de burbujas | Paint.reset y setAntiAlias en cada relleno de reserva, aunque el objeto ya conserva su estilo. | Limpiar solo el shader anterior y asignar color/alfa. Se conserva el antialias nativo. |

## Animaciones y apariencia

No se modificaron FastMotion, FastMotionTiming, curvas, duraciones, gestos,
preferencias ni las animaciones del sistema operativo. La mejora buscada consiste
en reducir trabajo por dibujo y evitar esperas de almacenamiento en UI.

Los bordes parciales y su shader de terminación ya tienen caché por celda;
BubbleFusion reutiliza el contorno nativo y no crea bitmaps/shaders por frame.
Se conservaron estas rutas: cambiar la silueta, desactivar glass o quitar efectos
sin mediciones no sería una optimización equivalente del producto.

## Verificación sin APK

Nueve pruebas nuevas en `tests/test_beta36_render_budget.py` ejecutan producción
o métodos de producción con colas, Canvas y vistas controlados:

- Peers de usuario/grupo/secretos, identificadores mayores de 32 bits, cuentas
  separadas, caché presente, entidad ausente y excepción de almacenamiento.
- Cuadrículas con coordenadas positivas, negativas, fraccionarias y alineadas;
  exclusión de regiones vacías/invertidas antes de crear nodos gráficos.
- Una captura para 10 000 solicitudes estáticas; recaptura al cambiar el origen;
  comprobación de composición al retirar todas las regiones.
- Geometría del hueco del contador con distintas densidades y escalas, ramas API
  anterior/posterior a 26 y reutilización del Path en 10 000 dibujos estables.
- Cambios de propiedades de vistas y rechazo de contenidos sucios.
- Ningún registro de fondo/actualización de refracción en 1 000 superficies opacas;
  restauración al volver a transparencia.
- Un observador externo para 1 000 suscripciones de una misma vista y liberación
  al desuscribir, limpiar y destruir.
- Una lectura del recurso para 1 000 instancias de LiquidGlassEffect, con 1 000
  shaders independientes y sin recreación del efecto con uniformes idénticos.

Estos son conteos en fixtures JVM, no porcentajes de mejora, tiempos de GPU ni
FPS del dispositivo. Se verifican también sintaxis Java y consistencia del diff.
La suite completa se ejecuta con `python -m pytest tests/ -q -p no:cacheprovider`.
Resultado final: **360 aprobadas, 39 omitidas, 0 fallos**. Las omisiones
corresponden a corpus externos de plugins, SDK/API Android o artefactos R8
ausentes; no se cuentan como pruebas aprobadas. Las nueve pruebas nuevas pasan.
La sintaxis de los nueve archivos Java modificados y la coherencia del paquete
y versión también pasan.

No se ejecutaron Gradle, assemble, generación/firma de APK ni despliegues.
El commit usa `[skip ci]` para no iniciar compilaciones automáticas por push.

## Lo que requiere la próxima beta en dispositivo

La precarga cubre la entrada `DialogsActivity.presentFragment(BaseFragment)`;
otras entradas a ChatActivity conservan su comportamiento nativo. La creación de
layouts, carga de mensajes y decodificación de medios siguen necesitando una
traza para localizar cualquier demora restante, incluso cuando el peer está en
caché. La compilación y el enlace completo de Android también quedan pendientes.

Comparar APK base y candidata en el mismo dispositivo, con las mismas cuentas,
contenido y ajustes, sin borrar sesiones. Separar primer acceso de accesos con
caché. Registrar modelo, Android, frecuencia de pantalla y configuración de efectos.

1. Repetir scroll/fling por lista de chats y conversaciones de texto y multimedia.
2. Abrir y volver de chats con caché y sin caché; comprobar toques consecutivos,
   salida de la pantalla y cambio de cuenta durante una lectura.
3. Probar blur/glass activados y desactivados, transparencia, temas claro/oscuro,
   bordes parciales, fusión, teclado, rotación y otra ventana.
4. Inspeccionar especialmente el borde del hueco de los contadores: el clip por
   Path necesita comparación visual en GPU real, especialmente en Android antiguos.
5. Medir frames lentos, p50/p95/p99 de duración de frame, toque a primer contenido,
   tiempo UI/RenderThread y memoria con Perfetto/FrameTimeline o herramientas Android.
   Comprobar reposo sin bucles nuevos y comparar varias repeticiones.

No se prometen FPS constantes ni ausencia total de lag sin esta validación física.

El verificador histórico `tools/identity/check_identity.py` exige literalmente
`1.0.0-beta.1`, por lo que tampoco acepta la base beta 35. No se usó como
validación de identidad de beta 36 ni se modificó su contrato histórico. El
paquete y la configuración de firma no cambiaron.
