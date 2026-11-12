# Cambios

## 1.0.0-beta.53 — build 1342

- Se recupera una presencia claramente visible de Rueda 3D, Perspectiva inclinada y Deslizamiento lateral en ambas listas. El objetivo de amplitud pasa de 0,30–0,85 a 0,65–0,90; se conservan el filtro de velocidad y la continuidad al invertir.
- Calibración intermedia entre beta 51 y beta 52: rueda nominal de 40°, perspectiva de 9°/4,5°/0,7° y lateral del 12 % del ancho, antes de modular por amplitud e intensidad. No se borran ni sustituyen las elecciones guardadas.
- Una animación de elementos deja de reiniciar el efecto de toda la lista. En la pantalla principal solo se excluyen las filas móviles que el animador nativo dibuja aparte, tanto del efecto como de su proyección de toque.
- Un contenedor de vídeo retenido pero retirado de la pantalla ya no cancela permanentemente los efectos de la conversación. Se mantiene la suspensión para vídeo realmente adjunto y menús externos.
- Se conservan la proyección 3D coherente, los pivotes suaves, las cachés acotadas y la salida de 96 ms al tocar sin retrasar la acción nativa. Nuevas regresiones de visibilidad durante un arrastre corto y lento en todos los niveles.
- Compilación oficial solicitada tras las pruebas locales; sin supervisión de progreso ni resultado.

## 1.0.0-beta.52 — build 1341

- Se reduce claramente la fuerza de los tres efectos en todos los niveles: Rueda 3D de 58° a 26°, Perspectiva de 13°/7°/1,8° a 5°/2,5°/0,4° y desplazamiento lateral del 18 % al 6 % del ancho, antes de modular por velocidad e intensidad.
- Velocidad filtrada y callbacks coincidentes agrupados; envolvente más suave de 0,30 a 0,85, sin impulsos por intervalos inventados. Se conserva el mismo motor e intensidad en ambas listas.
- Rueda 3D: separación de centros calculada con el ángulo realmente mostrado. Pivote estable en filas normales y transición gradual al pivote acotado de mensajes altos/álbumes, evitando saltos al cruzar bordes o cambiar de tamaño.
- El toque interrumpe la inercia nativa antes de entregar ese mismo DOWN, permitiendo abrir chats y pulsar burbujas sin un primer toque dedicado solo a frenar. La retirada visual parte de la pose mostrada, es monótona y termina en 96 ms sin bloquear la acción.
- Es posible retomar el arrastre durante la retirada. Se mantienen coordenadas del toque, deltas nativos, pulsación prolongada, selección y ciclo de vida. La intensidad intermedia pasa a llamarse Equilibrada; se conservan las elecciones guardadas.
- Se conservan las optimizaciones de matrices, álbumes y capturas. Pruebas locales sin empaquetar APK; la compilación se solicita por el workflow oficial y el propietario revisará su resultado.

## 1.0.0-beta.51 — preparación, build 1340

- Revisión de fluidez: inversión/salida con velocidad continua, una proyección compartida para Perspectiva y traslación directa para Deslizamiento lateral. Límites de álbumes reutilizados y pose coherente para captura/gestos. Intensidades conservadas; comparación de trabajo y regresiones en `docs/scroll/BETA51_SCROLL_EFFECTS_AUDIT.md`. Sin compilar APK.

- Pantalla principal → Animaciones al desplazarse: Sin efecto, Rueda 3D, Perspectiva inclinada y Deslizamiento lateral. La lista de chats y el interior de las conversaciones se configuran por separado.
- Intensidad compartida Suave/Marcada/Intensa, con Marcada como nivel inicial y efectos desactivados hasta elegirlos. Geometría normalizada y respuesta temporal comunes para ambas listas.
- Entrada, inversión y asentamiento continuos; sin bitmaps, capas adicionales, cambios de layout ni temporizadores permanentes del efecto.
- Se coordinan las capas de mensajes, fondos de álbumes, nombres, horas y reacciones. Las pulsaciones durante el efecto usan la proyección inversa y conservan las distancias nativas del gesto.
- Respeta animaciones desactivadas y exploración táctil; libera el estado al separar la lista. Preferencias persistentes e incluidas en FlexyStudio.
- Pruebas JVM y comprobación de tipos Android sin empaquetar la aplicación. Validación física de fluidez pendiente; no se compila APK en esta revisión.

## 1.0.0-beta.50 — build 1339

- Se retiran completamente la isla de notificaciones y Camera Pop: vistas, animaciones, índices, temporizadores, ajustes, recursos y enlaces de ciclo de vida.
- Se restaura el flujo normal de notificaciones de Telegram/Android, sin filtros de isla ni desvío de avisos. Los antiguos valores Solo isla ya no afectan al funcionamiento.
- Apertura de chats: las solicitudes simultáneas del mismo interlocutor comparten una lectura de almacenamiento y conservan sus callbacks.
- Los resultados tardíos se descartan si la cuenta cerró sesión, cambió de propietario o se recreó su controlador. Los datos recientes de la caché tienen prioridad sobre una instantánea más antigua de disco.
- Los callbacks y observadores temporales de precarga se liberan al cerrar sesión, incluso si la cola antigua se detuvo. Se permite reintentar una carga fallida sin dejar una solicitud bloqueada.
- Se conservan iconos, reproductor, pantalla principal por defecto y optimizaciones anteriores. Compilación oficial solicitada sin supervisión posterior.

## 1.0.0-beta.49 — preparación, build 1338

- Camera Pop evoluciona a una isla de notificaciones compacta, anclada al recorte real de cámara y con contadores agregados de chats/mensajes.
- Tocar la isla despliega una lista nativa con filas recicladas; solo tocar una conversación abre ese chat. Conserva privacidad, lectura sincronizada y silenciamientos configurables.
- Permite todos los chats de la cuenta o solo los elegidos; permanencia mientras haya pendientes, 1–9 segundos y otros intervalos, o duración personalizada de 1–300 segundos. El panel abierto pausa el ocultado.
- Movimiento propio con resortes críticamente amortiguados: al invertir o interrumpir el gesto conserva posición y velocidad. Sin blur, sombras pesadas ni callbacks de cuadros en reposo.
- Los avisos de mensajes se presentan por la isla con la app visible; en segundo plano se restaura la presentación Android sin borrar las colas nativas. Incluye opción explícita Solo isla, con explicación de su alcance.
- Los avisos esenciales de llamadas/reproducción y notificaciones no representadas por la isla conservan su tratamiento nativo.
- Recuperación inicial de chats en bloques, fotos solo para filas visibles, metadatos sin contenido de mensajes y tope de marcas de lectura antiguas. Sin APK compilada en esta etapa.

## 1.0.0-beta.48 — build 1337

- Camera Pop recibe eventos reales de mensajes directamente de NotificationCenter, independientemente del permiso Android y de las categorías globales de notificaciones de Telegram.
- Separa la recuperación de pendientes de la deduplicación de llegadas para no suprimir avisos inmediatos de personas o canales ya presentes en la caché.
- Con recordatorios activados, avisa en cada regreso a primer plano si los chats elegidos siguen sin leer, sin esperar al intervalo. Espera carga de caché, foco y contadores nativos.
- Conserva selección, privacidad y horario de silencio. El control de silenciamientos se limita a chats/temas silenciados expresamente y se explica en ajustes.
- La absorción termina en el centro real del recorte, con contracción progresiva, silueta vectorial de cuello y superficie opaca hasta entrar en el agujero. Sin desenfoque ni bucles permanentes.
- Pruebas de regresión para eventos nativos, recuperación frente a llegadas, notificaciones generales apagadas, contadores tardíos, foco y regreso con pendientes. Compilación oficial solicitada sin seguimiento del workflow.

## 1.0.0-beta.47 — build 1336

- FlexyBubble Camera Pop opcional en Ajustes de FlexyGram → Conversaciones, con selector nativo de chats/contactos/grupos/canales/bots por cuenta.
- Avisos de mensajes entrantes reales y recordatorios de pendientes, agrupación limitada, deduplicación, privacidad, silenciamientos, horario de silencio y demostración ficticia.
- Anclaje al recorte mediante APIs Android, alternativa con detector existente de Telegram y posición superior segura cuando no hay geometría válida.
- Entrada y absorción finitas hacia el recorte, sin blur ni redibujado permanente; pulsar cancela la animación y solicita abrir el chat inmediatamente.
- Temporizador solo con la app visible, revalidación al volver y limpieza en pausa/desactivación. No crea servicios ni permisos de superposición ni altera las notificaciones normales.
- Conserva las mejoras de arranque de beta 46 y la pantalla principal por defecto. Verificación JVM/API Android y guía manual en `docs/performance-current/BETA47_CAMERA_POP.md`; mediciones físicas pendientes.

## 1.0.0-beta.46 — preparación, build 1335

- Arranque: la creación de la carpeta de plugins y la migración/verificación de permisos pasan al executor del motor, antes de ejecutar Python. Con el motor apagado no se fuerza ese trabajo durante el inicio.
- Se agrupan las solicitudes de inicio del intérprete que estaban esperando en su executor; conservan sus callbacks sin repetir la preparación/importación después del primer resultado.
- Las preferencias de confirmaciones de bots web se abren cuando se usan; el cierre de sesión también limpia sus registros si el proceso no las había abierto todavía.
- Los seis TextPaint de tamaños de emoji se reutilizan sin perder actualizaciones de fuente/densidad, evitando recrearlos en cada inicialización de recursos.
- LeakDetector, sus registros, el detector ANR y la política VM de diagnóstico quedan bajo el indicador explícito `debugTools`; la beta normal evita sus exploraciones y GC forzados.
- Glyph: el enlace de servicio se pospone al callback tras la primera oportunidad de dibujar la interfaz; las entradas sin interfaz conservan el enlace inmediato.
- Trazas de carga nativa, idioma, configuración y recursos iniciales para medir el arranque en dispositivo. No se oculta el problema con una pantalla vacía o un temporizador.
- Sin APK compilada; permanece la pantalla principal por defecto de beta 45.

## 1.0.0-beta.45 — preparación, build 1334

- Se elimina el estilo de pantalla principal «Telegram iOS» y su selector. Queda únicamente la pantalla principal por defecto.
- Se retiran la cabecera/buscador específicos, los tamaños de filas y textos forzados y las reglas que impedían personalizar la barra inferior.
- Las preferencias antiguas de estilos esencial/iOS se restablecen a por defecto. Se admite el valor legado en copias de FlexyStudio para poder importarlas sin reactivar el estilo retirado.
- Se conservan las líneas divisorias, las mini píldoras, los avatares, los iconos originales y las mejoras de rendimiento/animaciones anteriores.
- Sin compilación de APK por indicación del usuario.

## 1.0.0-beta.44 — build 1333

- Pantalla principal: selector «Por defecto» / «Telegram iOS». Se retira «Diseño esencial»; su valor antiguo migra a «Por defecto».
- Cabecera con Editar, Chats centrado, composición con el icono oficial y búsqueda nativa recogible. Se conservan historias, carpetas, gestos y menús; Guardados permanece en la lista.
- Filas con avatares de 60 dp, márgenes del cliente de iPhone y textos de 17/16 sp; barra inferior flotante con Contactos, Llamadas, Chats y Ajustes. Cambiar de estilo restaura la configuración de navegación guardada.
- Material sobre el motor compartido de blur/glass y color opaco alternativo. Sin renderizadores de iOS, bitmaps adicionales por frame ni animadores permanentes.
- Fuente oficial fijada a `24638bc69bd083981b178dd1e7f921eebbf7fc46`; el material de UIKit se adapta a Android, sin afirmar identidad de píxeles o certificación de la versión de iOS.
- Incluye las mejoras de arranque y movimiento de mensajes de beta 42/43, aún no compiladas en esas revisiones.

## 1.0.0-beta.43 — preparación, build 1332

- Menú de mensajes/fotos: expansión anclada y elevación ligera de la selección, con un mismo reloj para tarjeta, burbuja y reacciones, siguiendo el patrón visual del video de referencia.
- Integración analítica local del resorte para estas interacciones: recorrido consistente con el tiempo real entre frames y sin un primer salto fijo. Se conserva el integrador existente de los demás consumidores.
- El desenfoque empieza a fundirse cuando la captura está disponible; se admite la entrega inmediata antes de crear el propietario y se descartan generaciones/cierres obsoletos.
- Retorno interrumpible conservando posición y velocidad; límites de fotos altas, cancelación de gestos y scroll estático conservados.
- Pruebas de frecuencias, frames irregulares, blur tardío y entrega síncrona; sin APK de esta revisión.

## 1.0.0-beta.42 — preparación, build 1331

- Arranque UI: cero y la cuenta seleccionada preparan sus controladores antes del contenido; las demás sesiones activas se distribuyen por la cola de frames existente. Entradas de servicio y cierres de sesión durante la espera mantienen un camino explícito.
- Galería: los cuatro registros binder de MediaStore pasan a la cola de trabajo; la suscripción global del reproductor deja de repetirse por cuenta.
- Proxy: se cancela el ping periódico al estar desactivado o no haber servidor seleccionado; reanudación por cambios nativos de configuración.
- Iconos: tabla primitiva compacta, sin crear 1.566 objetos de metadatos al cargar; originales, tamaños, tintes y asociaciones conservados.
- Notificaciones: se corrige la reprogramación del comprobador de retenciones de animación, con cancelación y reentrancia sin callbacks duplicados.
- Regresiones de orden, sesiones, worker, proxy y expiración; medición de asignación inicial del mapa en JVM. Sin APK de esta revisión.

## 1.0.0-beta.41 — preparación, build 1330

- Se sustituyen las hojas anteriores por 235 recursos originales de Telegram-iOS, revisión `24638bc69bd083981b178dd1e7f921eebbf7fc46`, con 1.566 asociaciones semánticas y trazabilidad de cada archivo.
- Navegación, conversaciones, ajustes, menús, llamadas, edición y reproductor utilizan originales donde existe una asociación verificada. La opción Cupertino anterior usa la misma importación oficial.
- Dimensiones originales en puntos trasladadas a dp, densidades de Android y proporciones conservadas; sin estirar símbolos en botones grandes. Sticker de esquina doblada y teclado mantienen estados distintos.
- Pestañas, menús de burbujas, controles musicales, flecha de navegación y vistas previas dejan de dibujar aproximaciones para los roles importados. Se conservan las áreas táctiles y los tiempos de FlexyGram.
- Recursos nativos con caché y estado independiente por control: 952.054 bytes de dibujos empaquetados, frente a 1.300.230 bytes de las hojas previas. Sin PDF, conversión ni reproducción Lottie nueva durante el dibujo.
- Alcance y excepciones documentados: no se certifica un port completo de iOS 27. 483 asociaciones del catálogo antiguo quedan con su recurso existente al no haberse establecido un equivalente exacto. Sin compilar APK.

## 1.0.0-beta.40 — preparación, build 1329

- Composer compacto: una única pasada del material nativo por cápsula/botón, igual que la cabecera. Se retira el tinte secundario que aplanaba visualmente el blur y la refracción de Liquid Glass.
- Se conservan la política global de efectos/ahorro, los colores propios del tema, las geometrías, los estados de grabación/envío y el fondo sólido al desactivar efectos.
- Regresión de composición única, opacidad animada, botones visibles, caché de radios y transición de políticas; fixture gráfico actualizado para representar el tinte que ya aplica el drawable nativo.

## 1.0.0-beta.39 — preparación, build 1328

- Navegación: precarga asíncrona de peers desde ActionBarLayout (presentación y restauración de pila), panel lateral y chats incrustados; se descartan respuestas obsoletas al navegar, pausar, cerrar o cambiar de cuenta.
- Reproductor Orbit: una captura regional compartida entre superficies visibles, resolución acotada, desenfoque asíncrono y recorte fraccionario por superficie. Observadores compartidos y liberación al cerrar; sin sondeo en reposo.
- Cola musical: normalización, filtrado y cálculo de diferencias fuera de UI; publicación de filas mediante DiffUtil y cancelación inmediata de consultas antiguas, cierres y arrastres.
- Perfilador: los módulos app.flexygram participan en la clasificación de código propio.
- Caché de la silueta de las superficies del reproductor; se conservan diseño, glass y animaciones existentes. Pruebas de concurrencia, recorte y ciclo de vida; sin APK nueva.

## 1.0.0-beta.38 — preparación, build 1327

- Iconos predeterminados del ZIP del propietario: 119 símbolos originales en cinco densidades, con 477 asociaciones semánticas revisadas. Se conservan los estados o acciones sin equivalente en las hojas.
- Entrada de texto: sticker de esquina doblada para abrir el panel; se conserva el teclado para volver a escribir.
- Ajustes: iconos de 36 dp con categorías coherentes, tinte del tema y espacio para títulos largos/RTL; se eliminan las capas de fondo de los símbolos.
- Bitmaps compartidos mediante la caché nativa de recursos, sin decodificación durante el dibujo ni relojes nuevos. Los packs elegidos por el usuario conservan su prioridad.
- Integridad de PNG, regeneración, densidad, aislamiento de tinte y regresiones de ajustes comprobados sin generar APK.

## 1.0.0-beta.37 — preparación, build 1326

- Cola temporal: reproducir a continuación, añadir al final, quitar pendientes y reordenar mediante asa o acciones accesibles. Conserva canción, posición, aleatorio y repetición; no modifica listas guardadas.
- Buscador por título, artista y archivo, accesible desde el reproductor ampliado y dentro de la cola.
- Portada circular con arco luminoso y punta degradada del color de acento del tema; degradados reutilizados, sin blur ni reloj adicional.
- Cabecera, tamaños y alineación de título/favorito ajustados a la referencia aprobada.
- Contorno ondulado del botón del reproductor minimizado activo solo durante reproducción visible. El ampliado conserva su círculo sin ondas.
- Regresiones de cola, concurrencia al arrastrar, búsqueda, recursos y presupuesto de dibujo; sin generar APK.

## 1.0.0-beta.36 — preparación, build 1325

- Apertura desde la lista de chats: precarga asíncrona de usuarios, grupos y chats secretos ausentes en caché; las respuestas de navegación obsoletas se descartan.
- Contadores de navegación inferior: recorte directo del hueco del contador, con geometría reutilizada, sin capa intermedia por contador.
- Blur: límites de captura correctos para coordenadas negativas y bordes alineados; invalidación por posición, tamaño, transformaciones y contenido pendiente de dibujo.
- Glass: fuente del programa compartida e inmutable; shaders y uniformes independientes por superficie. Se evita registrar fondos que una superficie opaca no muestra.
- Seguimiento de posiciones en otras ventanas: un observador por vista, liberado al desuscribirse o destruir el propietario.
- Burbujas adaptativas: conservación del Paint de relleno y limpieza explícita de su shader, sin reinicializarlo en cada dibujo.
- Pruebas de regresión y auditoría en `docs/performance/beta36-audit.md`. Sin APK generada ni mediciones físicas de FPS/jank en esta revisión.

## Sin publicar — preparación 1.0.0-beta.1

- Certificado público Beta registrado por indicación del propietario; huella fijada, generación de sustitutos deshabilitada y firma Alpha intacta.

- Nueva variante `beta`, paquete `com.flexygram.messenger`, nombre FlexyGram y versión prevista `1.0.0-beta.1` (código 1287).
- Procedimiento de custodia local, dos backups cifrados y verificador público/PKCS12 sin Android; certificado oficial registrado; backups pendientes de confirmación.
- Firma Beta independiente, con certificado fijado por su SHA-256 y sin sustitución por firma debug o Alpha.
- Recursos de cuentas, contactos y shortcuts separados por identidad; iconos aprobados conservados.
- README, créditos y guías de compilación, migración y custodia de firma.
- Validación estática específica sin compilar Android.

No hay APK ni Beta publicada en esta etapa. La base es el candidato Alpha 1286 del PR #130, `258dd3590f40ca0083a4b7bad6b413433c4e2c14`; PR #129 y #128 permanecen en su ascendencia. Los tres figuran como borrador, sin fusionar, en la inspección del 29 de octubre de 2026. La entrega Alpha previa no valida la nueva identidad Beta.

El historial técnico anterior se conserva en Git y en los registros de `tools/connected_alpha`; no se convierte en una lista ficticia de versiones estables.
