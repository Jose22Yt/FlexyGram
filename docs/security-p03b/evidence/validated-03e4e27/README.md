# Evidencia original recuperada — P0.3b

Código validado: **03e4e27e3a59b79b05f3b99b6fdee7d48709bc16**. Integración aprobada en develop: **5443f15ac61309bc9bfc9a8f81d0d028e9479923**. Ambos árboles coinciden: aab7e88c522c1df18bd3f028b9eb40fd9ec431af.

Estos son los bytes de logs/resultados recuperados, con hashes verificados, del archivo original FlexyGram-P03b-PR7-evidencias-03e4e27.zip (SHA-256 c385a24aba868a4485ae6dd70e5d461fdbce7509ebf61eaa0f44a3669abb1e39), conservado en Work. No son logs recreados o pruebas nuevas del commit documental. El archivo original completo conserva también los demás controles y herramientas. No contiene APK ni material privado de firma.

- [tests.log](tests.log): 26/26, cero fallos/omisiones, 8,565 s.
- [build.log](build.log): ARM64 completo con JNI/Chaquopy, sin SKIP, BUILD SUCCESSFUL 9m55s; 244 tareas (40 ejecutadas / 204 al día tras aprovisionamiento del mismo checkout).
- JSON *.result identifica exactamente el commit ejecutado. artifact-summary y translator-findings identifican el APK interno por SHA-256; no distribuyen el APK.
- [SHA256SUMS.json](SHA256SUMS.json) conserva los hashes originales de los archivos incluidos.

Resultados históricos inmutables: no se recompiló por añadir estos documentos. El PR #7 ahora está fusionado; los flags de estado de otros documentos anteriores son instantáneas históricas, no estado actual. Android real, restauración/OEM y compatibilidad 16 KB siguen pendientes. La comprobación genérica de APK sin claves sigue fallando por las dos claves cliente de traductores.
