# Revisión de ajustes repetidos

Se revisaron los índices compactos, la propiedad de las filas nativas, las
opciones heredadas y las rutas de búsqueda/enlaces compartidos. Los accesos de
búsqueda a un mismo editor no se consideran configuraciones independientes.

## Ubicaciones únicas

Los siguientes accesos heredados se suprimen de las listas adicionales y se
redirigen al editor nativo existente, conservando callbacks y preferencias:

| Ajuste | Ubicación |
| --- | --- |
| Credenciales de Cloudflare para transcripción | Conversaciones → Fotos, vídeo y voz |
| Clave de Gemini para transcripción | Conversaciones → Fotos, vídeo y voz |
| Credenciales de OpenAI para transcripción | Conversaciones → Fotos, vídeo y voz, al seleccionar OpenAI |
| Estilo de texto | Conversaciones → Menús y acciones |
| Filtrado de contenido sensible | Sistema → Privacidad y diagnóstico |
| Conjuntos de emoji | Sistema → Emoji |
| Ocultar reacciones | Pantalla principal → Elementos visibles, con controles por tipo de chat |

OpenAI y el acceso condicional a modelos Vosk ahora tienen propietario explícito
en el filtro de filas multimedia; no quedan excluidos al abrir el apartado.
Los enlaces antiguos de las opciones consolidadas y los resultados de búsqueda
resuelven la ubicación canónica antes de intentar abrir el editor heredado.

No se borran ConfigItems, claves guardadas, credenciales ni estados del servidor.
La migración existente de HideReactions a canales/grupos/privados se conserva
sin modificaciones. Los controladores y diálogos de las funciones se reutilizan.

## Verificación

Los tests JVM ejecutan el filtro de extras real y comprueban que ninguna de las
siete claves aparece en las rutas heredadas, que existe el destino canónico y
que siguen disponibles los controles nativos y condicionales. Se vigilan también
las colisiones entre alias nativos y propietarios heredados, la migración de
reacciones y el orden de resolución de búsqueda y enlaces.

La revisión es de código y pruebas aisladas; no sustituye una revisión visual
exhaustiva en dispositivo. No se compila APK ni se inicia GitHub Actions.

Resultado final: **423 pruebas aprobadas y 39 omitidas**. Los cuatro archivos
Java modificados pasan el análisis sintáctico. Queda pendiente la comprobación
visual en un dispositivo; no se generó ninguna APK.
