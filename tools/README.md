# Herramientas de desarrollo

Las utilidades se organizan por componente. Ejecuta cada herramienta desde la raíz del
repositorio y consulta su guía antes de usarla. Las entradas privadas y las salidas
locales deben permanecer fuera del control de versiones.

| Carpeta | Propósito |
| --- | --- |
| `settings_monet` | Originales aprobados e importación reproducible de iconos de ajustes. |
| `ios_originals` | Fuentes, procedencia y conversión de recursos originales de Telegram para iOS. |
| `ios_bubbles` | Verificación de geometrías y selectores de estilos. |
| `navigation`, `native_context` | Comprobaciones de navegación y menú de mensajes. |
| `delete_motion`, `opex_motion` | Pruebas de movimiento e interacción. |
| `signing` | Utilidades de firma bajo custodia del propietario. |
| `beta_release`, `beta_integration` | Verificación de identidad e integración de variantes. |
| `variant_checks` | Comprobación de separación de las tareas de validación Alpha y Beta. |
| `connected_alpha` | Contratos y fixtures históricos asociados a revisiones concretas. |

Los manifiestos, hashes, parches y recursos originales que usan los contratos históricos
son entradas de prueba, no cachés. Sus resultados corresponden a sus commits de referencia;
no acreditan una compilación ni un rendimiento actual.

Las comprobaciones principales se describen en la [guía de pruebas](../tests/README.md).
La compilación integrada se describe en [BUILDING.md](../docs/BUILDING.md).
