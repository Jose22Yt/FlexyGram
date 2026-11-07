# Beta 14: integración

Base: beta 13 (`1749b71ce`). Entregas de Codex 2 integradas:
`76596b5a05e02c1d31f321a91334dc19bf8c5d80` y
`47e3138e0412ccf403fd24a6d9f5cd2a75d54f31`.

Resolución de diferencias:

- Se conserva el modo inicial original y todas las preferencias explícitas del
  usuario. Tarjetas esenciales, Signature, blur, glass y reducción de animaciones
  siguen siendo opcionales.
- El reproductor compacto de Codex 2 es la única interfaz de música en la beta,
  siempre activa por decisión del usuario. Conserva el motor nativo de audio.
- Cupertino permanece como pack opcional (ID 3); no sustituye el pack original.
  Su código archivado por Codex 2 queda fuera de la aplicación. El código activo
  continúa en `TMessagesProj/src/main/java/app/flexygram/icons`.
- Ambos materiales personalizados de burbujas conservan los efectos compartidos
  (blur, transparencia, borde y fusión). El modo «Por defecto» omite esas
  superficies sin borrar sus parámetros. Esto preserva la personalización
  solicitada en esta sesión frente a la retirada de controles en `76596b5a0`.
- Se conservan las optimizaciones de cierre de menús, callbacks de animación,
  recálculos de vista previa y limpieza de capturas aportadas por Codex 2.
- Se conserva la corrección local de transparencia inferior durante capturas de
  menús, incluidas las restauraciones ante excepciones.
- FlexyStudio conserva el nuevo selector de cambios individuales y sus catálogos
  incluyen los valores iniciales originales y el nuevo estilo de pantalla.

Versión prevista: `1.0.0-beta.14`, código `1303`, ARM64.
