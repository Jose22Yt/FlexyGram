# De una APK privada a una prueba Android autorizada

FlexyGram, responsable @Lukhou23. Herramientas host; no habilitan servicios, firma,
instalación ni distribución. Rama independiente apilada sobre PR23 `40c80878…`.
PR17 `b637c290…` y PR24 `db5b9a11…` se inspeccionaron sin modificarlos.

## Comprobación de cada build

Python 3.11 y `pyelftools==0.32`; reutiliza `tools/beta_development/review_apk.py`,
`tools/native_compatibility/{audit,acceptance}.py` y el escáner de traducción.
Con `ANDROID_SDK_ROOT` y `JAVA_HOME` del entorno de compilación:

```bash
python3.11 tools/beta_handoff/gate.py --apk "$PRIVATE_APK" --sha256 "$APPROVED_SHA256" --classes "$MATCHING_JAVA_CLASSES" --output "$PRIVATE_REPORT"
```

Usa Build Tools36.0.0 y NDK27.2.12479018 por defecto; admite sus rutas explícitas.
Versión esperada13.0.2/1261; cambiar ambos argumentos sólo al aprobar una versión nueva.
No recompila ni invoca ADB. Debe preservarse el directorio de clases Java del MISMO
build para el control `javap` heredado: esas clases externas **no prueban por sí
solas los valores de campos DEX**. El informe declara esa limitación. El hash
aprobado liga los bytes al build revisado; nuevos builds requieren revisión de
sus evidencias y, posteriormente, ejecución autorizada de las guardas.

Primero comprueba hash, ZIP/CRC, inventario/rutas/recursos indispensables y ausencia
de firma; después versión/paquete/manifiesto, políticas, ELF/dependencias/símbolos,
PT_LOAD/RELRO y zipalign16KB, más el escaneo dirigido heredado. Conserva el control
de los cuatro ELF reconstruidos. Cualquier fallo deja exit1 e informe BLOCKED,
incluso si había un PASS viejo en la ruta de salida. No presenta stderr de herramientas.
Un PASS estático no certifica arranque, JNI/Python ni fluidez Android.

Correcciones demostradas al verificador PR23: ahora exige ApplicationLoader y un
único filtro MAIN con LAUNCHER en el alias público. Mantiene la categoría opcional
MULTIWINDOW_LAUNCHER del manifiesto actual. Las dos pruebas negativas fallan antes
del parche (`evidence/manifest-before.log`) y pasan después.

## Respaldo privado y recuperación

El archivo original de Work2 NO está disponible en esta sesión. Ni la APK
`98de352740b07c3e6f00a2399246c9c60bc744ed44a976324c79e4132b086afd`
ni el ZIP de44 miembros fueron recuperados o vueltos a verificar aquí.
El ZIP exterior registrado por PR23 tiene SHA256
`9cad4dc2accdeb0fc6260ad889882b159fee11710f2c39213cae2c50a6ae8634`.
No se reutilizan sus resultados como nueva inspección de bytes.

La vía preparada oficial de almacenamiento volvió a fallar con un ZIP sintético
sin APK/secretos: HTTP403 en `hosted apps tools/list`, antes de transferencia.
La lectura/listado privados sí respondió. No se puede concluir que el tamaño,
ZIP, cuota o una URL caducada sean la causa. Hace falta restablecer el acceso
al descubrimiento de herramientas de esa vía en la sesión que conserva el ZIP.
No se probó otra cuenta, destino público ni atajo de transferencia.

Una vez disponible el ZIP original, verificar sin extraer:

```bash
python3.11 tools/beta_handoff/archive.py inspect --bundle "$PRIVATE_ZIP" --bundle-sha256 9cad4dc2accdeb0fc6260ad889882b159fee11710f2c39213cae2c50a6ae8634 --apk-sha256 98de352740b07c3e6f00a2399246c9c60bc744ed44a976324c79e4132b086afd
```

Comprueba digest exterior, todos los bytes/CRC, rutas/inventario y una sola APK con
hash esperado. No presupone el formato del manifiesto privado de Work2. Para una
APK nueva, `archive.py create --apk ... --apk-sha256 ... --bundle ...` crea un
contenedor mínimo0600, exclusivo, con recibo; `verify` lo relee. Este contenedor
no sustituye el respaldo completo de JNI, clases Java, insumos y logs de Work2.
Nunca sobrescribe archivos existentes ni extrae miembros a rutas arbitrarias.

Pasos de conservación: (1) conservar original local y hashes; (2) usar helper oficial
vigente con el lote completo; (3) retener identidad/versionado privado devuelto;
(4) descargar de nuevo a otro directorio con el helper de lectura; (5) ejecutar
`inspect` y gate sobre los bytes recuperados, comparar los hashes; (6) sólo entonces
marcar recuperación remota verificada. Las herramientas locales siempre devuelven
`private_persistence_confirmed=false`: no pueden atestiguar una transferencia remota.
Nunca subir APK/wheels/JNI/claves a GitHub. No borrar el original mientras falle el paso4.

## PR24 y primer arranque

No se duplica ni cambia su protocolo. Sobre un checkout separado del PR24 fijado:

```bash
python3.11 tools/beta_handoff/diagnostics.py --source-dir "$PR24/tools/beta_diagnostics" --output "$PRIVATE_SYNTHETIC_REPORT"
```

Exige hashes de los dos módulos revisados antes de importarlos. Ejecuta un escenario
sintético con el paquete beta, fatal Java/ANR/carga nativa/Chaquopy y exclusión de un
paquete con sufijo. Genera un plan de captura, sin ejecutar ADB. Las métricas sin
observaciones quedan ausentes. Los0 del hash de esa fixture NO identifican una APK.
Para resultados reales usar `capture.py`/`analyze.py` originales con metadatos del
hash real y los eventos del productor que integrará Work2; no inventar latencias.

## Revisión independiente de startup del PR23

- Alias público apunta a BetaPreviewActivity no exportada; paquete propio y backup
  deshabilitado. Las categorías reales están preservadas por el nuevo gate.
- BetaPreviewActivity.onCreate comprueba identidad/capacidades antes de crear rutas;
  ApplicationLoader.onCreate ocurre antes y carga JNI. Un fallo de carga allí puede
  impedir incluso llegar a esa Activity: requiere primer arranque Android/Logcat.
- postInitApplication inicializa controladores comunes; las guardas de políticas
  siguen siendo necesarias además del manifiesto sin INTERNET. No se declara que
  los constructores sean seguros en ART sólo por inspección.
- LatestNavigation cancela pendientes en pausa/Back y se cierra al destruir.
  No se cambia la cola ni ActionBarLayout en esta misión.
- Python arranca bajo demanda fuera de UI; el resultado vuelve al hilo UI y comprueba
  Activity destruida. Cambiar tema reconstruye las vistas: probarlo mientras Python
  está pendiente para detectar resultados dirigidos a una celda anterior. Esto es un
  caso de laboratorio pendiente, no un crash demostrado ni un parche improvisado.
- No se reproduce la corrección NotificationCenter ni el productor de eventos:
  corresponden a Work2. No hay evidencia nueva de un defecto del cliente que justifique
  cambiar su comportamiento aquí. Los defectos demostrados corregidos son del gate.

## Puerta antes de firma/instalación

1. Respaldo remoto recuperado y bytes aprobados; clases Java y evidencias del mismo build.
2. Host aislado autorizado, sin USB/cuentas/datos personales, offline demostrado y
   espacio para AVD/artefactos. Usar preflight/launcher existentes: ARM64 API24/4KB y
   API35+ con páginas reales16KB, compatibilidad retroactiva desactivada. No repetir
   en este host los intentos de aislamiento ya bloqueados.
3. Gate estático y revisión del delta del build. Production y seis capacidades cerradas.
4. Custodia recuperable de clave Diagnostic/beta y autorización **independiente** para
   generar/firma; después autorización de instalación sólo en laboratorio. Ninguna concedida aquí.
5. Registrar hash firmado, certificado y relación con el unsigned mediante verificador
   posterior a firma existente/contrato beta independiente; no alterar contratos históricos.
6. Primer arranque: Logcat acotado al PID/paquete, JNI/Python,12 casos nativos por perfil,
   lifecycle, cambio de tema durante Python, navegación/toques/cancelación. Captura privada;
   compartir sólo informes agregados saneados. Usar PID nuevo tras cada reinicio.
7. Vincular fallos al hash/commit/perfil/página reales y reproducir cada defecto antes de
   parchearlo. Comparaciones de rendimiento sólo bajo condiciones equivalentes y varias
   repeticiones. La beta offline no es todavía un cliente autenticable.

Work2 puede incorporar estas herramientas y el parche del verificador mediante cherry-pick
tras revisión. PR23/24/17 y main/develop permanecen sin cambios; no hay firma ni ejecución Android.
