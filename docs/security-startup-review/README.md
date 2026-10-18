# FlexyGram 1.0 — revisión de seguridad y arranque del Paso 3

Proyecto creado y dirigido por **@Lukhou23**. Se conservan los créditos y licencias de Telegram, Exteraless y sus dependencias. Fecha de revisión: 2026-10-18 UTC.

## Dictamen

**No se ha demostrado la causa del incidente. El Paso 3 debe permanecer abierto.** Hay riesgos estáticos confirmados que deben corregirse mediante un cambio posterior aprobado antes de otra prueba autenticada: secretos en registros, credenciales y servicios heredados, respaldo de tokens y ausencia de una identidad Android independiente.

No se encontró una llamada automática a `auth.resetAuthorizations` en las rutas de arranque examinadas. Las dos instanciaciones localizadas corresponden a la pantalla de sesiones y requieren interacción y confirmación. Esto no demuestra que nunca se ejecutaran en el teléfono, ni descarta un plugin, código dinámico, otro cliente o una decisión del servidor. No se reproduce el incidente ni se certifica que el cliente esté libre de vulnerabilidades.

El cierre de sesiones y la invalidación/congelación de bots se conocen **por el relato del responsable**. No se recibieron registros de Telegram, una cronología corroborada ni trazas del dispositivo. No se verificó desde su cuenta la autenticidad del aviso atribuido a `@AbuseNotifications`. La coincidencia temporal con la instalación no establece causalidad.

## Objeto y procedencia

| Elemento | Identificación |
| --- | --- |
| Fuente exacta compilada e inspeccionada | `082aff3d0fc57ce90b0154fe76d9d7c796ed45a2` |
| Referencia original registrada | `1ad6a60a6834ffca722b1a22f4fba27ecb29a061` |
| APK investigada, conservada localmente | `FlexyGram-1.0-Clean-Baseline-arm64-debug.apk` |
| SHA-256 recalculado en esta revisión | `1ca683e5e4ef924ca9e7636afcd0c0b2c54de5064a46603ac5ae7b4f811278fe` |
| Tamaño | 111994391 bytes |
| Identidad verificada en el Paso 3 | `com.exteraless.app`, `13.0.2 (1261)`, ABI instalable `arm64-v8a` |
| Firma verificada anteriormente | Android Debug, APK Signature Scheme v2 |
| SHA-256 del certificado | `ba687de28eaaaa20bc77898f5520ba1b544216c6a3b88c333a96e593b3e94456` |
| PR #2, revisado al comenzar esta auditoría | Abierto, sin fusionar; cabeza `61035fe977c251aef81b13324c46926ed2a61e3b` |
| Teléfono | Poco X8 Pro / MediaTek 8500 Ultra / Android 17 / HyperOS 4: datos comunicados por el usuario, no comprobados aquí |

No se recompiló ni se distribuyó otra APK. La fuente se revisó en el commit exacto del artefacto; la cabeza posterior del PR #2 documenta esa compilación. El hash histórico `bd1865…` corresponde a otro archivo y no se utiliza como identidad de esta APK. Integridad criptográfica y compilación exitosa no prueban seguridad, fluidez ni funcionamiento real.

## Documentos y cobertura

1. [Autenticación, claves, sesiones y llamadas de revocación](AUTHENTICATION.md).
2. [Credenciales, paquete, respaldo, servicios y actualizador](CONFIGURATION.md).
3. [Arranque, hilos y comparación Debug/Staging/Release](STARTUP.md).
4. [Bibliotecas nativas, Python/JNI y páginas de 16 KB](NATIVE.md).
5. [Plan seguro, datos mínimos del teléfono y cierre del Paso 3](SAFE-TEST-PLAN.md).
6. [Evidencia estructurada y localizadores reproducibles](evidence.json).

## Niveles de evidencia

| Nivel | Significado |
| --- | --- |
| Confirmado estáticamente | Código/configuración o estructura binaria inspeccionados; no implica ejecución |
| Verificado en archivo | Hash/estructura de la APK y evidencias de herramientas, sin ejecutar Android |
| Reportado | Observación del usuario sin corroboración independiente |
| Hipótesis condicionada | Mecanismo técnicamente posible, necesita condiciones y evidencia adicional |
| Desconocido | Depende del estado privado del teléfono o de información del servidor no disponible |

No hay mediciones de arranque, experimentos de autenticación ni pruebas de instalación en esta auditoría. Las comprobaciones anteriores tampoco incluyeron ejecución Android. No se emplearon cuentas, contraseñas, OTP, sesiones ni llamadas de revocación reales.

## Hipótesis del incidente: mecanismo y límite

| Hipótesis | Evidencia disponible | Qué permitiría discriminarla sin experimentar |
| --- | --- | --- |
| Decisión de seguridad/antabuso del servidor | Compatible con el aviso descrito y con efectos sobre bots; razón específica desconocida | Cronología y aviso redactado; confirmación por soporte oficial solicitada por el titular |
| Credenciales API heredadas/configuración ajena | API ID efectivo 6 y hash fallback coincidente, confirmados; no se documentó titularidad propia | Procedencia administrativa de credenciales; eventuales códigos RPC ya existentes, saneados. No se afirma que ID 6 por sí mismo cause sanciones |
| Terminación desde la interfaz de sesiones | Call sites concretos y confirmaciones encontrados; ejecución desconocida | Recuerdo de las acciones realizadas, fecha y antigüedad de la nueva sesión; no volver a pulsar para reproducir |
| Duplicación de una clave MTProto | Mecanismo documentado por Telegram; no hay `AUTH_KEY_DUPLICATED` observado | Indicar actualización/restauración/clonación/migración, sin copiar archivos de sesión; error ya registrado si existe, depurado localmente |
| Exposición de secretos por logs o respaldo | Sumideros de logging y BackupAgent confirmados; acceso/exfiltración no demostrado | Indicar si se exportaron logs o restauraron datos; no compartir logs completos ni buscar tokens en el teléfono personal |
| Plugins o modo desarrollador | Capacidades y controles encontrados; motor apagado por defecto; uso real desconocido | Indicar si se activaron motor/plugins/modo inseguro/desarrollador y su procedencia, sin ejecutarlos otra vez |
| Otros clientes, automatizaciones o compromiso anterior | No auditados; no hay evidencia para atribuirles responsabilidad | Cronología privada del titular y soporte; esta auditoría no permite descartarlos |
| FCM, paquete compartido o desalineación ELF como causa directa | Riesgos diferentes confirmados; no se encontró mecanismo que por sí solo explique toda la secuencia | Separar fallos de entrega push, conservación de datos y fallos del linker de sanciones del servidor |

No se asignan probabilidades inventadas. Las llamadas ordinarias de cierre de sesión no explican por sí solas la congelación de bots. Tampoco se halló en las rutas revisadas una automatización de BotFather para invalidar tokens. Esta búsqueda no sustituye una auditoría completa de todas las dependencias, binarios y posibles plugins instalados.

## Correcciones propuestas, todavía no implementadas

| Prioridad | Propuesta para revisión | Criterio de aceptación posterior |
| --- | --- | --- |
| P0 | Retirar tokens, claves push y otros secretos de todos los sinks de logs, incluido servidor de desarrollo | Pruebas locales con canarios sintéticos: ningún secreto llega a Logcat, archivo ni informe de fallos, en ninguna variante |
| P0 | Eliminar fallback autenticable y exigir credenciales propias; mientras falten, diagnóstico sin autenticación ni conexión Telegram | La configuración incompleta bloquea la funcionalidad de autenticación antes de cualquier petición; no imprime valores |
| P0 | Identidad diagnóstica y firma propias; sin importación de datos, respaldo ni actualización heredada | Coexiste con Exteraless/Telegram; no utiliza sus cuentas, preferencias, providers o sesiones |
| P0 | No continuar pruebas con la cuenta personal ni redistribuir esta APK como apta para iniciar sesión | Aprobación del informe y plan, seguida de pruebas aisladas y offline |
| P1 | Revisar Firebase/OAuth/passkeys/maps/billing y la política de almacenamiento de tokens | Propiedad/restricciones documentadas o servicio desactivado en diagnóstico; restauración y borrado probados sin secretos reales |
| P1 | Resolver las cuatro dependencias Python con PT_LOAD de 4 KB mediante reconstrucción/actualización controlada | Auditoría ELF/ZIP, imports Python y cargas JNI en Android 4 KB y 16 KB; no eliminación de componentes |
| P1 | Instrumentación de tiempos y errores con etiquetas fijas y sin contenido privado | Trazas reproducibles del arranque; separación de UI, JNI, almacenamiento y Python |
| P2 | Evaluar optimizaciones únicamente tras medir y aprobar el alcance | Ninguna optimización, interfaz, animación, navegación o función se cambia en esta etapa |

## Control de cambios y límites

Se verificó que la conexión GitHub corresponde a `Jose22Yt` y dispone de escritura en este repositorio. Esta entrega se publica en una rama documental separada basada en `develop`; no cambia código funcional ni el PR #2. `main` y `develop` conservan sus SHA anteriores y no se fusiona ningún PR.

No se habilitaron Actions ni se ejecutaron workflows: la consulta de ejecuciones devolvió cero. El conector rechazó la lectura de la configuración administrativa de Actions; **cero ejecuciones no certifica por sí mismo que el interruptor global esté desactivado**. Se conserva su estado sin modificarlo; el responsable puede confirmarlo en Settings → Actions → General. No se crea Release.

Recomendación: conservar esta APK como evidencia, detener nuevas pruebas autenticadas y revisar las propuestas P0. Después de aprobación explícita, un cambio controlado del propio Paso 3 podrá preparar la identidad diagnóstica aislada y ejecutar las puertas de validación del [plan](SAFE-TEST-PLAN.md). No declarar el Paso 3 terminado ni comenzar el Paso 4 hasta cerrar esas puertas o aceptar expresamente los pendientes.
