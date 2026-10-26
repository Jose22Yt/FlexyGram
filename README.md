<div align="center">
<img src="tools/connected_alpha/identity/flexygram-blue-original.png" width="128" alt="Logotipo de FlexyGram">

# FlexyGram

**Tu Telegram, a tu manera.**

Cliente Android no oficial que utiliza la API de Telegram, con personalización nativa Signature y una prioridad constante: estabilidad, respuesta táctil y fluidez.

**Creador y responsable: @Lukhou23** · **Cuenta GitHub: [Jose22Yt](https://github.com/Jose22Yt)**

[Proyecto](https://github.com/Jose22Yt/FlexyGram) · [Desarrollo](https://github.com/Jose22Yt/FlexyGram/pulls) · [Incidencias](https://github.com/Jose22Yt/FlexyGram/issues) · [CI](https://github.com/Jose22Yt/FlexyGram/actions) · [GPL-3.0](LICENSE)
</div>

## Estado del desarrollo

FlexyGram está en **Connected Alpha**, preparando su primera Beta. Ya existe código funcional, integración continua y un proceso real de compilación, firma y verificación ARM64. La distribución de las Alpha firmadas es privada; los informes o imágenes de CI no equivalen a una APK descargable.

| Referencia | Estado verificable |
| --- | --- |
| [Alpha 1274, PR #95](https://github.com/Jose22Yt/FlexyGram/pull/95) | Base integrada aprobada para esta auditoría: `8d4fe2f0a7d47e05a34c2a2c7fc8c706ed781881`. [CI de refinamiento aprobada](https://github.com/Jose22Yt/FlexyGram/actions/runs/40237236269). |
| Alpha 1275 | Trabajo activo de Work 1 en `integration/alpha1275-signature-performance-ui`; no se anuncia como versión terminada ni validada físicamente. |
| Beta 1.0 | Preparación y auditoría. No se declara publicada, aceptada en dispositivo ni lista para distribución general. |

Las primeras pruebas físicas de Connected Alpha fueron confirmadas por el propietario. Cada revisión posterior necesita su propia validación: no trasladamos automáticamente esa aceptación a otra Alpha. Las mediciones de host o ensayos Android aislados tampoco demuestran mayor velocidad que Exteraless en un teléfono.

## La experiencia FlexyGram

- **Signature Native:** identidad propia, Home, cabecera, compositor iPhone, burbujas y superficies Pearl/Midnight, desarrollados sobre las vistas existentes.
- **Signature Music:** reproductor, minirreproductores y representación compacta, conservando el motor multimedia nativo.
- **FlexyStudio — Comparte tu FlexyGram:** exportación, intercambio e importación nativa de archivos `.flexyGram`, con validación y lista explícita de preferencias admitidas. La base 1274 amplía el esquema de la primera entrega; consulta [su registro real](TMessagesProj/src/main/java/app/flexygram/studio/core/StudioSchema.java) antes de prometer una categoría.
- **Personalización compatible:** ajustes Signature y mecanismos nativos de temas e iconos; las sesiones y el transporte de Telegram siguen siendo responsabilidad de su arquitectura original.
- **Ingeniería de rendimiento:** herramientas reproducibles, reducción selectiva de trabajo y pruebas de regresión. El objetivo de igualar o superar a Exteraless necesita mediciones comparables, no porcentajes supuestos.

Son componentes presentes en el código integrado, no una garantía de que todos los escenarios estén aprobados físicamente. Consulta la [matriz pre-Beta](docs/PRE_BETA.md) para límites, bloqueos y pruebas pendientes.

## Tecnología y desarrollo

Android nativo con Java/Kotlin, componentes de Telegram/Exteraless, MTProto, bibliotecas JNI y reproducción multimedia existentes. Chaquopy integra el entorno Python heredado; FlexyStudio no usa el intérprete de plugins para aplicar configuraciones. El proceso Connected Alpha compila y verifica la aplicación real, incluidos sus componentes nativos.

- [Compilar y validar la base actual](docs/BUILDING.md)
- [Contribuir y coordinar trabajos](CONTRIBUTING.md)
- [Auditoría de identidad Android](docs/ANDROID_IDENTITY.md)
- [Actualizador: auditoría y propuesta todavía desactivada](docs/UPDATER.md)
- [Preparación para Beta 1.0](docs/PRE_BETA.md)

No se incluyen capturas antiguas, montajes ni renders de pruebas como si fueran pantallas aprobadas de esta versión. Las capturas reales se añadirán cuando estén identificadas por versión, aprobadas y libres de información privada. El logotipo mostrado reutiliza el archivo de identidad ya incorporado al proyecto; no sustituye los recursos activos del launcher.

## Origen, licencias y agradecimientos

FlexyGram es un fork de [Exteraless](https://github.com/exteraless/exteraless), con código y recursos procedentes de Telegram, NagramX, exteraGram y otros proyectos. Su desarrollo propio no implica autoría de los componentes heredados.

La licencia principal es **GNU GPL versión 3**: [LICENSE](LICENSE). Se conservan el historial, los avisos de copyright y las condiciones particulares de bibliotecas y recursos. Los iconos y diseños heredados de exteraGram mantienen los créditos a **@the8055u** y **@BlueprintDsgn**. No se presume que la licencia del código conceda derechos sobre todos los recursos gráficos.

Consulta [procedencia y agradecimientos](docs/UPSTREAM.md), [inventario de atribuciones](docs/ATTRIBUTIONS.md) y la [documentación original archivada](docs/upstream/README.exteraless.md). FlexyGram utiliza la API de Telegram y no es una aplicación oficial de Telegram.
