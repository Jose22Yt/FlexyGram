# Cambios

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
