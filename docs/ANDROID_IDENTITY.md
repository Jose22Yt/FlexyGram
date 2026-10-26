# Auditoría de identidad Android

Base Alpha1274: `8d4fe2f0a7d47e05a34c2a2c7fc8c706ed781881`. El [inventario reproducible](prebeta/identity-inventory.json) contiene recursos, literales, referencias de marca, etiquetas del manifest y permisos. Un recurso existente no demuestra que una pantalla lo muestre actualmente: las filas de revisión requieren trazar su llamada y el locale/build type efectivo.

## Hallazgos comprobados

| Área | Evidencia | Resolución recomendada |
| --- | --- | --- |
| Identidad común | `res/values/strings.xml:AppName` = exteraless; `values-es/strings.xml:AppName` = Nagram X | Corregir valores visibles, conservando el nombre de recurso; revisar variantes y todos los locales |
| Nombre obtenido por código | `LocaleController.getAppName()` usa `OpenExtera`, cuyo valor común sigue siendo exteraless; su fallback literal también | Cambiar valor/fallback, sin renombrar `LocaleController` ni sus claves |
| Etiqueta Android | Manifest usa `@string/NagramX`; el overlay Connected Alpha ya lo resuelve a **FlexyGram Alpha** | El identificador heredado no es por sí mismo un fallo. Verificar manifest/APK combinados y label instalado; no cambiar el componente por cosmética |
| Notificaciones | `NotificationsController` usa AppName y NagramX en distintas rutas | El resultado puede diferir por clave/locale. Probar notificación general, chat, medios y segundo plano con los recursos corregidos |
| Compartir / selector Android | Labels de application, activities y aliases; llamadas de AndroidUtilities a getAppName | Verificar APK/selector, grants content URI y accesos directos después del parche; no renombrar authorities ni permisos |
| Título personalizado | `CustomTitleHint` dice Leave blank to use exteraless | Localizar pista EN/ES/RU sin alterar la preferencia del título personalizado |
| Bienvenida | SignatureWelcome usa FlexySignatureName/Tagline y referencia compartida del avión | Identidad principal propia presente; revisar que la explicación de cliente no oficial/API Telegram sea suficientemente explícita en intro y descripción |
| Acerca de / créditos | About de FlexyGram y créditos propios ya existen; NekoAboutActivity conserva @NagramX y repositorio/crowdin heredados | Mantener upstream en créditos. Revisar rutas heredadas; no inventar un canal de soporte oficial a partir de un nombre de usuario |
| Actualizador | REPO y User-Agent heredados, enlaces a releases | Mantener gate Alpha; ver [UPDATER](UPDATER.md). Cambiar solo REPO no basta para hacerlo seguro |
| Iconos / launcher | Aliases históricos y preferencias seleccionadas | Conservar aliases, migration receiver, IDs y mecanismos de Work1. Revisar textos de créditos y autorización de recursos, no sustituir launcher |

## Parche preparado, no aplicado

`tools/connected_alpha/prebeta/android-identity.patch` contiene únicamente sustituciones de valores de AppName/AppNameBeta/NagramX/OpenExtera/CustomTitleHint, overlays Connected Alpha EN/ES/RU y el fallback de `LocaleController.getAppName`. No modifica manifest, aplicación ID, paquetes, clases, bases, preferencias, servicios, authorities, launcher, navegación, sesiones o transporte.

Se genera desde los blobs de la base aprobada. `prepare_identity_patch.py` es determinista. Las pruebas aplican el parche **solo en un directorio temporal**, comprueban los únicos recursos autorizados, preservación de claves/atribuciones, sintaxis XML y reversión. El enlace AAPT2 de prueba verifica las entradas nuevas; no equivale al manifest integrado ni a una APK real.

Tras Alpha1275, revisar el HEAD nuevo y sus archivos activos antes de ejecutar `git apply --check tools/connected_alpha/prebeta/android-identity.patch` en una rama de integración. Después aplicar y validar ahí, no sobre la rama activa de Work1 sin coordinación. El manifest puede conservar `@string/NagramX`: se conserva la clave y cambia su texto. Beta/estable necesitan una decisión explícita de branding de canal; no se cambia applicationId para quitar el sufijo Alpha.

## Conservar por compatibilidad

`org.telegram.*`, `app.exteraless.*`, clases y aliases, `exteraless_updater`, preferencias existentes, proveedores, rutas de datos, permisos personalizados, nombres JNI y gitlinks no son etiquetas que puedan reemplazarse masivamente. Los avisos de copyright, nombres de dependencias y enlaces de agradecimiento son atribuciones, no fallos de branding. El inventario los clasifica aparte o pide revisión contextual.

Esta rama cambia documentación y herramientas, no los recursos Android de producción. Por tanto, **los nombres heredados señalados siguen presentes en la aplicación de base** hasta integrar y compilar el parche.
