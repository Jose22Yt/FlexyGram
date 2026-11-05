# Desarrollo y compilación

## Elegir la base

Este repositorio contiene distintas líneas de desarrollo. Consulta la rama y el commit de la entrega que quieras reproducir; no asumas que la portada o `main` contienen la beta más reciente.

```sh
git clone --recurse-submodules https://github.com/Jose22Yt/FlexyGram.git
cd FlexyGram
git switch <rama-elegida>
git submodule update --init --recursive
```

## Entorno

Usa las versiones de JDK, SDK, NDK, CMake y Gradle declaradas por la rama y sus workflows. Los requisitos pueden cambiar entre variantes. Revisa `TMessagesProj/build.gradle`, `gradle/wrapper/gradle-wrapper.properties` y `.gitmodules` antes de descargar o ejecutar herramientas.

Configura tus propios identificadores de API y servicios, y las credenciales de firma cuando correspondan. Mantén los valores privados en `local.properties`, variables de entorno o secretos de CI; no los añadas al repositorio ni a los comandos de incidencias. Un archivo Firebase de otra aplicación no sustituye el registro de tu propia variante. La configuración heredada `TMessagesProj/google-services.json` se retira del control de versiones: debes proporcionar la tuya en la ubicación que requiera tu variante. La entrega beta privada utiliza un secreto de CI y no necesita publicar ese archivo. Una compilación local que use el plugin de Google Services requerirá esta configuración antes de ejecutarse.

## Verificar y construir

Consulta las tareas y variantes de Gradle de la rama seleccionada. Las variantes de prueba y distribución pueden usar aplicaciones, firmas y servicios distintos. No distribuyas una compilación como oficial sin comprobar identidad, procedencia y firma.

Las comprobaciones de documentación y fuentes pueden ejecutarse sin generar APK. Las pruebas Android, la compilación completa y las pruebas de rendimiento en dispositivo son etapas diferentes: registra exactamente qué comprobaste.

## Dependencias

Los componentes nativos pueden requerir submódulos y herramientas adicionales. Conserva las licencias incluidas y consulta [CREDITS.md](../CREDITS.md). Nunca sustituyas dependencias faltantes por archivos descargados de una procedencia no verificada.
