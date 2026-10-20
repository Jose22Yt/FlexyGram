# Exportación móvil futura — código pendiente de ejecución

Base congelada de PR23: 958d28ba7ded7e0fa868a71788d8c0679d53bda4.
Durante la sesión Work2 avanzó a090b907cfd305614130fe35340bd148bc247dcff:
únicamente tres documentos de recuperación/firma, sin solapamiento con este parche.
PR31 consultado: 93af93d45fb918a8d6ae79dac3ef2ec6cdac7219.
Rama/PR independientes: no se altera la APK ya compilada, su firma temporal,
PR23, main, develop ni herramientas/contratos históricos ADB.

Implementación limitada a betaDevelopment:
- Botón Exportar diagnósticos en Settings; ACTION_CREATE_DOCUMENT/application/zip,
  CATEGORY_OPENABLE y EXTRA_LOCAL_ONLY. Sin permiso adicional, FileProvider,
  ACTION_SEND, persistencia de grants, Internet ni servicio.
- Reutiliza BetaEventExport/NavigationEvents sin modificarlos, en localRuntime ya
  existente. Persistencia privada y ZIP completo ANTES del selector; sin E/S de
  archivo en UI. Inactivo no crea tareas, proveedores ni capturas nuevas.
- Sólo session_id actual, export_id1..N contiguos y sus dos archivos fijos. Valida
  el formato canónico del productor: campos/operaciones/fases/clocks permitidos,
  contadores/orden/records y límites (100 lotes,16MiB descomprimidos). Un cambio de
  formato del productor exige revisión; no se aceptan campos nuevos silenciosamente.
- ZIP: <session>_<id>/{observer.json,events.jsonl}, más diagnostic.json con schema,
  kind, probe/probe_outcome enumerados y runtime_certified=false. Los lotes
  extraídos pasan al MISMO import_events.assemble de PR26; no se crea otro importer.
- No lee Logcat/preferencias/bases/sesiones/mensajes. No serializa exceptions/URI
  ni identifica usuarios. Rechaza enlaces/rutas fuera de las carpetas permitidas.
- Snapshot privado retenido al cancelar/fallar. Retry sin re-drain; éxito libera
  sólo la referencia UI para preparar otro snapshot, sin borrar lotes/ZIP privados.
  Escritura al provider sólo en worker y sólo URI content seleccionada; errores
  de open/write/close no deben anunciar éxito. Puede quedar documento externo
  parcial (reintentar, no borrar automáticamente documentos del usuario).
- Restaura únicamente el nombre validado de snapshot en Bundle para resultado del
  selector tras recreación; no guarda URI, credenciales ni estado READY. Callback
  débil descarta Activities destruidas. Un proceso destruido durante preparación
  puede conservar lotes privados sin que la nueva Activity recupere el trabajo
  en curso: no se declara exportado ni se reanuda un servicio permanente.

Estado de verificación de ESTA sesión:
**0 pruebas ejecutadas; 15 métodos nuevos preparados, sin PASS declarado.**
exec_command devolvió "No usable execution environment is available".
No se ejecutaron Python, javac, SDK/Gradle, teléfono, emulador, firma o APK.
No confundir comparación estática de fuentes con compilación Android.

Para la sesión con ejecución, antes de incorporar en una beta futura:
    FLEXYGRAM_DIAGNOSTICS_SOURCE=<PR24/tools/beta_diagnostics> python3.11 -B -m unittest discover -s tests/beta_development -p test_mobile_document.py -v
    FLEXYGRAM_DIAGNOSTICS_SOURCE=<PR24/tools/beta_diagnostics> python3.11 -O -B -m unittest discover -s tests/beta_development -p test_mobile_document.py -v

Requiere JAVA_HOME=JDK21. Los doubles se amplían sólo para Intent/ContentResolver/
Uri/resultados del selector; las pruebas compilan fuentes reales (--release8),
ejecutan cancelación/retry/recreación/errores y puente real ZIP→PR26. Luego ejecutar
la suite beta completa por el cambio de Activity/doubles; no sumar resultados
históricos como nueva ejecución. Compilar SDK/JNI/Chaquopy sólo en otra etapa
autorizada, NO durante esta misión ni sobre la APK en firma.

Android17: se usan API existentes del SAF, sin permisos de almacenamiento nuevos.
**Compatibilidad real NO verificada**: selector HyperOS, concesión content URI,
rotación/muerte del proceso, almacenamiento lleno, cancelación, close del provider,
copia ZIP y fluidez durante escritura deben probarse en el teléfono con nueva APK.
startActivityForResult es API heredada/deprecada pero se conserva aquí para no
añadir dependencias ni cambiar la arquitectura Activity existente.

La validación nativa propuesta es necesaria pero no suficiente para certificar
API24/Android17. Nunca habilita Production, autenticación, plugins o servicios.

Fuente oficial SAF:
https://developer.android.com/training/data-storage/shared/documents-files
