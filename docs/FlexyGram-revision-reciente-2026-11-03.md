# Revisión de funciones recientes y recompilación

Revisión del 3 de noviembre de 2026 del repositorio `Jose22Yt/FlexyGram`.
Rama de aplicación: `codex/flexygram-beta-glass`, fuente revisada
`765bec55777b381ad5b56d5d92d070ff58c05c2d`.

Al consultar las ramas remotas no se encontraron commits posteriores a esa
fuente. `main` continúa en `5b07b41af5bdf6419a1fe88eff121285323deede`.
Las funciones siguientes son incorporaciones recientes ya integradas, no cambios
nuevos realizados durante esta revisión.

| Función | Evidencia de integración y alcance |
| --- | --- |
| Conversiones rápidas en mensajes | Integrado `2ed2f7b8f`. Se activa en Chat → Mensajes e interacción → Conversiones rápidas. Convierte unidades y horarios; inicialmente desactivado. Las divisas no tienen proveedor de tasas, por lo que no ofrecen un resultado monetario. |
| Mensaje a sticker | Integrado `32ece2175` y renombrado a FlexySticker. La acción del menú de mensaje abre una vista previa con envío directo y guardado en favoritos. |
| Member Lens | Componentes `app.flexygram.memberlens` y acceso desde el avatar de un participante en ChatActivity, condicionado al contexto y su configuración. Facilita consultar mensajes de ese participante. |
| Ajustes y vistas previas Signature | Secciones nativas de personalización, paletas adaptativas y vistas previas de los componentes del cliente. |
| Barra inferior personalizable | Compactación, pestañas visibles, intercambio de posiciones mediante arrastre en la vista previa y búsqueda circular separada. |
| Blur y rendimiento | `765bec557`: corrige dependencias del interruptor retirado de Liquid Glass, reutiliza las fuentes del fondo y mueve el cálculo CPU de blur de confirmación del teléfono a una cola de trabajo. |

## Compilación comprobada

La ejecución [41569324369](https://github.com/Jose22Yt/FlexyGram/actions/runs/41569324369)
terminó correctamente: pruebas, ensamblado, comprobación de firma y bibliotecas
ARM64, e incorporación del APK como artefacto. El artefacto del APK figura con
83,2 MB, frente a 99,9 MB del artefacto de la ejecución anterior 41560561310.
Estos valores son tamaños publicados de los artefactos descargables; no son una
medición del tamaño instalado ni una comparación de rendimiento en dispositivo.

La nueva compilación solicitada se activa publicando este informe en la misma
rama, mediante `ui-beta-debug.yml`. Conserva el código de aplicación revisado y
el perfil `flexyPerformanceBuild=true`, con firma de prueba y arquitectura
ARM64. No sustituye la compilación privada de la beta oficial.
