# Respuesta y cierre interrumpible de las burbujas

El menú compacto mantenía desactivado el scroll hasta finalizar el retorno, y
el contenido del chat rechazaba eventos mientras existía la vista seleccionada.
Además podía esperar la detección de idioma y pedir dos capturas de blur para
una misma apertura.

- El scroll, cursor y accesibilidad del chat se liberan al comenzar el cierre.
  La ventana se vuelve no táctil, no enfocable y no modal mientras termina el
  retorno visual.
- Un nuevo DOWN, scroll (incluido el de accesibilidad) o Atrás termina ese retorno
  antes de procesar la interacción nueva. Se completa también cualquier apagado
  de scrim pendiente, incluso si su animador de duración cero esperaba un frame.
- El controlador conserva posición y velocidad al retargetear. Su entrada tiene
  menos rebote y un límite de 360 ms; el cierre termina al cruzar el objetivo o
  alcanzar 180 ms. No se deja un callback de frames activo en reposo.
- El menú compacto aparece sin esperar la detección de idioma; su resultado
  posterior comprueba a qué mensaje pertenece. La ruta clásica conserva su
  arbitraje nativo durante la espera.
- La apertura compacta pide una única captura de blur. El foco diferido comprueba
  la identidad de la ventana para no reclamar foco desde un menú anterior.

Validación local: suite completa de 215 pruebas aprobadas y 31 omitidas, más
comprobaciones específicas de las rutas finales de toque y Atrás; Java y diff
válidos. Se prueban los controladores e integrador reales con un reloj simulado
a 60/90/120/144 Hz, cierre durante la entrada, interrupción inmediata, limpieza
exactamente una vez, ausencia de invalidación en reposo y descarte de owners
anteriores. La entrada se estabilizó entre aproximadamente 258 y 271 ms en esas
simulaciones. Estos resultados no son FPS ni latencias medidos en teléfono.
