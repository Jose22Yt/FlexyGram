# beta69: material nativo de chat, acento y estilo de interruptor

Base cf8580e6e4b083b69fce5dde2b740b1a2090305b; versión1.0.0-beta.69-chat-materials,
código1358, mismo paquete de la prueba nativa optimizada.

## Interfaces de conversación

Se retiran los bloqueos NATIVE_BASELINE_TEST que impedían drawSignatureNativeGlass
y la preparación/selección de materiales compactos. El diseño modifica geometría;
la fuente, fábrica, blur, shader LiquidGlassEffect y política son los nativos.
Los controles de ahorro de energía/HWA y los fallbacks legibles siguen en vigor.
No se clona ChatActivity, se cambia el layout ni se superpone otro motor de blur.

Los cuatro materiales de islas solo se crean si la presentación compacta y los
efectos están activos; el modo clásico no los construye. Se conservan en la vista
y se reutilizan (prueba10000 solicitudes ->4 creaciones; clásico/efecto OFF ->0).
Los flags de propiedad de dibujo y snapshots continúan restaurándose al finalizar
la captura; envío/voz conservan controles y gestos nativos.

En la galería de Interfaz superior o Interfaz inferior se incorpora el mismo ajuste
«Acento del tema en interfaces del chat», predeterminado OFF. Es compartido por ambas
superficies. Mezcla RGB8% del acento windowBackgroundWhiteBlueHeader, como las tarjetas,
sin alterar alfa de los materiales, contenido de mensajes ni flags globales de efectos.
La primitiva accentTint se comparte con SettingsCardStyle; sus colores actuales no
cambian. Los providers de chat siguen siendo BlurredBackgroundColorProviderThemed.
Las superficies sólidas y previews también reflejan el matiz; volver desde Ajustes
actualiza materiales aunque los flags de blur/glass no hayan cambiado.
Preferencias independientes flexy_conversation_surfaces/theme_accent, cacheadas:
10000 lecturas/peticiones no vuelven a abrir preferencias ni repiten escrituras.

## Interruptores

General -> Superficies y efectos visuales -> Estilo de interruptor permite escoger
FlexyGram o Contorno con cruz y marca. Se conserva el default2 existente; la nueva
variante usa el valor3 de la preferencia SwitchStyle ya existente. Se añade también
la etiqueta a la lista de estilos del editor de opciones heredado para que el índice
sea válido allí. Se reutiliza drawCustomSwitch: cápsula contorneada/cruz apagada,
relleno y marca encendida, colores del tema/Monet, estado y accesibilidad nativos.
El renderer Extera actual (valor2) conserva su ruta; no se añade otro motor o listener.
La prueba ejecuta el cuerpo real de dibujo con hosts explícitos de Canvas/tema y
comprueba contorno, cruz, marca, círculo y conservación del dispatch del estilo2.
No es una comparación de píxeles con la captura del usuario.

## Retorno del dock con Kyant ON

El usuario reportó persistencia del fallo tras beta68: no se considera aceptación
física de aquella corrección. Se registra ahora una comprobación única antes del
primer dibujo al reanudar/mostrar/enfocar el host, tras resolver visibilidad/layout.
El listener se elimina después de ejecutarse y también al ocultar/separar la vista.
No hay sondeo, retraso fijo ni reloj de dibujo continuo.

onHostResume renueva la clave de las capas del material si existe una composición:
una composición pausada puede coalescer ocultar/mostrar y conservar capas obsoletas.
Se renueva solo el material opcional del dock, preservando pestaña, preferencia,
posición y geometría nativas. Una composición ausente se crea en el pre-draw cuando
la vista está adjunta. La propiedad de dibujo/accesibilidad nativa se mantiene hasta
que el material está listo. El test comprueba ciclos de ventana, renovación de clave,
fallback, ejecución única del pre-draw y limpieza. Hardware/composición publicada
son entradas explícitas del test; no se afirma que la GPU del teléfono esté validada.

El rebote global, FlexyFiles, FlexyStudio y reproductor propio permanecen retirados
del perfil nativo. No se modifican cuentas, sincronización ni ruta SQLite de chats.
Los FPS, tiempos de arranque y aceptación visual final requieren la APK en el teléfono.
