# Evidencias del Paso 3

Los JSON contienen observaciones reales del entorno, entradas descargadas, submódulos, prebuilts y APK. Los logs publicados son copias depuradas de rutas locales y posibles valores de servicio; no se alteraron resultados ni mensajes técnicos de error. Las primeras comprobaciones fallidas de configuración corresponden al proxy local temporal. La comprobación posterior de configuración y la construcción ARM64 terminaron con exit 0.

`maven-cache-observed.json` es un inventario de archivos descargados (incluye metadatos y versiones que podrían haber sido descartadas durante resolución); no es el grafo final seleccionado ni una SBOM completa. `prebuilts-sha256.json` identifica entradas del checkout; no acredita su regeneración desde fuentes. `apk-verification.json` incluye los assets Python anidados, por lo que sus indicadores globales difieren de los limitados a lib/arm64-v8a. Los avisos ELF de 16 KB son resultados estáticos, sin ejecución en un dispositivo.

Se conserva la firma Debug únicamente como certificado público y huella. No se incluyen keystores, claves privadas, credenciales propias ni configuración local privada.
