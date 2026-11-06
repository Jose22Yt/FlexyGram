# Barra inferior y capturas de menús

Se corrigió una fuga de estado en `ChatInputViewsContainer.dispatchDraw`:
una captura mediante Canvas software marcaba las superficies glass como no
utilizadas y llamaba a `setAlpha(0)` sobre los drawables compartidos con la
pantalla acelerada. Esos drawables modifican la opacidad de sus RenderNodes, por
lo que la barra podía desaparecer aunque su vista siguiera visible.

La captura ya no oculta esos RenderNodes. Sus indicadores temporales de fondo
(píldora, micrófono y envío) y la máscara de superficies dibujadas se restauran en
`finally`, incluso si la captura falla. El cambio no crea bitmaps ni animadores
adicionales. Los cambios reales de estilo siguen ocultando superficies sobrantes.

El fondo del hijo se invalida solo cuando cambia su propietario. El pase normal
publica el estado una vez, después de dibujar las superficies, evitando alternar
falso/verdadero e invalidar continuamente cada frame.

Las pruebas ejecutan el método de producción con Canvas/drawables simulados:
1.000 capturas consecutivas sin redibujar la pantalla, errores durante captura,
canales, apagado real del fondo y ausencia de invalidaciones repetidas.

No se ha verificado físicamente el video adjunto: supera el límite de transferencia
de 32 MiB del entorno. No se ha generado una APK en esta corrección.
