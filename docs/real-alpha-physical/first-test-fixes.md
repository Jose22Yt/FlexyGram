# Primera prueba física: correcciones sobre PR #51

Base exacta: a91d006ec945c9d775d52db180f35884d77533e9. Evidencia: comentario 6342293683. No se ha ejecutado esta revisión en Android ni firmado su APK.

## Inspección de cuenta

El adaptador comparaba el directorio canónico de cuenta con su ruta absoluta sin resolver el alias del directorio privado. Esto rechazaba directorios vacíos válidos, incluso después de comprobar que ambas raíces privadas eran la misma. La regresión `androidProbeTrustedRootAlias` falla con el adaptador de PR #51 y pasa con la corrección. Es una causa reproducida en host, aún no atribuida al Poco: el mensaje anterior ocultaba todos los motivos.

Se compara ahora con el hijo esperado de la raíz privada canónica. Se siguen rechazando raíces ajenas, redirecciones del hijo, identidades existentes, preferencias de autorización y archivos tgnet. No se elimina ni lee contenido de autorización. Los controladores siguen solicitándose después de los rechazos por evidencia persistida.

Los rechazos muestran `ACCOUNT_INSPECTION:<Diagnostic>:<Step>`, exclusivamente enumeraciones cerradas: cuenta existente, archivos de autorización, material protegido, inspección no disponible, controlador no disponible, inicialización fallida, acceso denegado, E/S o excepción interna. No se incluyen rutas, identificadores, valores ni excepciones originales.

Regresiones añadidas: alias vacío en slots 0/1, alias con archivo protegido intacto, hijo redirigido rechazado y fallo de almacenamiento con diagnóstico seguro.

## Búsqueda offline

Las copias generadas de Apps, canales, multimedia, hashtags y publicaciones terminan en estados vacíos nativos sin esperar respuestas remotas. El inventario y sus hashes comprueban nueve fuentes offline; las fuentes originales y la política de capacidades permanecen intactas. La selección sigue limitada a realAlphaDebug con ambos opt-ins.

## Pantallas oscuras

Revisado el ciclo de vida: `BOOTSTRAP.ensure` ejecuta inicialización de aplicación y acceso a controladores síncronamente antes de `super.onCreate`; es un candidato para la demora inicial, no una causa medida. No explica por sí solo las transiciones ni demuestra un fallo de renderizado. El vídeo no permite asignar duración/causa con precisión. No se cambian el orden de inicialización, las comprobaciones de seguridad ni animaciones por conjetura.

## Siguiente ensayo (tras autorización separada de firma)

Modo avión, datos ficticios: abrir Login local > SMS/APP. Debe aparecer PhoneView; usar únicamente el código local 000000. Si se bloquea, capturar el código completo con Diagnostic y Step sin borrar datos. Comprobar Apps/canales/multimedia/hashtags/publicaciones con y sin consulta, Atrás, tema y reapertura. Grabar arranque frío y vuelta desde segundo plano por separado para medir los intervalos oscuros. No declarar pantallas nativas probadas antes del ensayo físico.
