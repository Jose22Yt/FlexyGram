# Proveedores de divisas: investigación, ninguno activado

Consulta documental del 2 de noviembre de 2026. No se ha llamado a una API de cotización ni añadido claves/endpoints al cliente.

| Alternativa | Procedencia y cobertura | Licencia/condiciones y decisión |
|---|---|---|
| BCE directo | Referencias frente al euro y un conjunto limitado de monedas; comprobar cobertura exacta antes de habilitar, sin prometer COP o toda ISO4217 | El BCE las publica como información y desaconseja su uso transaccional. Revisar el aviso de reutilización y atribución aplicable. No activado. |
| Frankfurter | Agregador de bancos centrales/fuentes oficiales; catálogo de cobertura dinámico, tasas combinadas o proveedor fijado | Código/documentación MIT; las tasas tienen condiciones de cada proveedor. Una tasa combinada no es una tasa oficial institucional. Revisar cada fuente elegida y cobertura necesaria. No activado. |

Referencias primarias leídas:
- https://frankfurter.dev/license/
- https://frankfurter.dev/
- https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html
- https://www.ecb.europa.eu/stats/pdf/exchange/Frameworkfortheeuroforeignexchangereferencerates.en.pdf

Antes de una futura autorización: fijar proveedor y cobertura permitida, cumplir atribución/términos, documentar indicación frente a uso transaccional y distinguir fecha de publicación de fecha de consulta. Tratar respuestas como no confiables: ISO, valor decimal positivo/finito/rango razonable, fuente y fecha obligatorias; rechazar timestamps futuros e incompatibles. El contrato Quote exige procedencia y BigDecimal, pero no sustituye estas validaciones del futuro adaptador.

Política propuesta para el adaptador futuro: LRU de como máximo 64 pares+fuente, vigencia basada en fecha publicada y calendario de la fuente (no convertir una tasa antigua en «actual» al volver a consultarla), deduplicación por par/fuente, cancelación de callbacks de vistas cerradas, vencimiento explícito y etiqueta visible si se permite una tasa anterior. No habrá polling en reposo. Solicitudes sólo ISO origen/destino: sin texto, importe completo del mensaje, cuenta, peer, nombre, contacto o sesión. Ninguna de estas peticiones está implementada/activada en este PR.
