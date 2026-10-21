# realAlpha: login nativo local integrado

Base PR #42: `57e3d958d161d77f3c468dcd9dc45644ccbc2fe7`.
Código de integración: `9acdc1d0811ce4772fe9487f8dad4b16fc0576f6`.
PR #43 en borrador, apilado sobre #42; no fusionar ni firmar/instalar.
FlexyGram — @Lukhou23, con procedencia, créditos y GPL de Telegram/Exteraless conservados.

La rama incorpora selectivamente los cinco módulos de #35–#40. El menú **Login local**
se añade a DialogsActivity nativo; ofrece SMS, APP, 2FA y registro simulados. Se construye
LocalLoginSession y se vincula a LoginActivity antes de admitir el fragmento en LaunchActivity.
No hay una interfaz de login alternativa. Código de prueba: `000000`; usar sólo ceros
para el teléfono y datos ficticios para contraseña/nombres. 2FA es una respuesta/proof
sintética, no una validación criptográfica ni autenticación. Completar muestra el estado
local; nunca entra en un cliente autenticado ni llama onAuthSuccess.

Los puertos sólo existen en la selección realAlpha opt-in. El diario/inventario son un
modelo en memoria: no describen ni escriben los archivos MTProto reales; commit está
denegado. Antes de crearlo, un attestor JNI de sólo lectura comprueba política/proceso/
cuenta y TelegramAccountAdapter rechaza identidad o archivos de autorización previos.
No se borran esos archivos para superar el control. QR, términos y demás rutas siguen
bloqueados; no cambian permisos, manifiestos, credenciales, capacidades ni firma.

Los originales LaunchActivity (incluido fix biométrico), DialogsActivity, LoginActivity y
las tres clases realAlpha quedan byte a byte iguales a #42. La selección genera una
copia de LoginActivity con los guards #40 y otra de RealAlphaActivity con la admisión y
ciclo de vida locales; Bootstrap y Policy se copian idénticos. Con la propiedad apagada
no se cambian las fuentes de ninguna variante. Con ella encendida sólo realAlphaDebug
es elegible. StartupDiagnostic queda explícitamente bloqueado para no superponer sus
instrumentaciones sin revisión. No aplicar de nuevo los parches 0001/0003: Gradle ya
contiene la selección. JNI añade únicamente el puente read-only cuando la opción está ON.

Dos defectos del host nuevo se reprodujeron en pruebas: un menú retenido llamaba al
host cerrado tras recrear la Activity, y el fragmento interno retenía fuertemente ese
host. Se rebindea el listener y se utilizan referencias débiles/fragmento estático.
Cancelación y destrucción invalidan la admisión y cierran buffers/propietario/hilo;
reabrir el laboratorio crea otro ensayo vacío, sin reanudar solicitudes ni sesiones.

## Continuar la compilación sin repetir la integración

Preparar los SDK/NDK y submódulos fijados del expediente #42, incluidas las dependencias
privadas verificadas. Este checkout no tiene los insumos/cachés de Work 2. No cambiar
versiones, usar SKIP ni relajar TLS para conseguir compilar.

```sh
python3.11 tools/real_alpha_local_login/materialize.py
NATIVE_TARGET=arm64-v8a ./gradlew :TMessagesProj:assembleRealAlphaDebug \
  -PflexygramRealAlpha=true -PflexygramLocalLoginPages=true --no-daemon
```

Usar JDK21, Gradle9.7.1, AGP9.3.1, SDK37, BuildTools36.0.0, NDK27.2.12479018,
CMake3.31.6 y Python3.11/Chaquopy17 fijados. El generador falla si los originales/hashes
no coinciden o existe una copia generada diferente. Conservar fuera del destino cualquier
copia previa antes de regenerar; no reemplazar fuentes compartidas ni el APK de #42.

**Resultado real aquí: BUILD FAILED**, durante settings al resolver Foojay1.0.0, también
con un intento online que conserva TLS. Además faltan SDK37/BuildTools/NDK/CMake y los
submódulos no están inicializados. No se alcanzó compilación Android Java, JNI o Chaquopy;
no hay APK unsigned nueva, SHA ni respaldo de binario que se puedan entregar.
[Entorno, intentos y submódulos](evidence/environment.json).

## Validación disponible y pendientes

[Resultados, IDs, comandos y hashes](evidence/results.json): **33 nuevas +5 de limpieza =38
pruebas distintas**, normal y Python -O: **76 ejecuciones finales PASS**, cero fallos u
omisiones. Se compilan módulos/host con JDK21, los métodos Android del adaptador contra
SDK24 con dobles Telegram/UI, y se carga el puente JNI real en una JVM Linux con la política
cerrada. Se ejecutan los bloques Groovy de selección con sourceSets simulados y el gate
Production original. LoginActivity/RealAlphaActivity completos se parsean, no se typecheckean.
Los fallos preliminares de los fixtures y los dos defectos reproducidos se conservan sin
sumarlos al conteo final. No son pruebas Android.

Falta: build Android completo (incluido Kotlin, sourceSets reales, duplicados, D8/JNI/
Chaquopy), verificadores adaptados al build con laboratorio y recuperación privada del
unsigned. Después, con autorizaciones separadas, comprobar en Android el menú nativo,
Phone→APP/SMS→2FA/registro, Atrás/cancelación, IME, temas, transiciones, recreación y
reaperturas. No se declara compatibilidad Android17 ni fluidez real de esta integración.
No se publican binarios ni se modifican #40, #42, main/develop o Actions.
