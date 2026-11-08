# FlexyGram — Directrices Oficiales para Desarrolladores y Agentes de IA

> **DOCUMENTO DE LECTURA OBLIGATORIA PARA CHATGPT, CODEX, CLAUDE, CURSOR, COPILOT Y DESARROLLADORES**
> Este repositorio contiene el código fuente de **FlexyGram**, un cliente avanzado de mensajería para Android basado en Telegram y Exteraless.

---

## 1. Identidad y Estado del Proyecto

- **Nombre de la Aplicación:** FlexyGram
- **Package Name (ID de Android):** `com.flexygram.messenger`
- **Versión Activa Oficial:** Definida dinámicamente en `gradle.properties` (`BETA_VERSION_NAME` y `BETA_VERSION_CODE`, actualmente `1.0.0-beta.27` / Build `1316`)
- **Rama Oficial de Desarrollo:** `codex/flexygram-beta-glass`
- **Repositorio Oficial:** `https://github.com/Jose22Yt/FlexyGram`
- **Huella Digital del Certificado Oficial (SHA-256):**
  `e71c4d1e14dd940892009c61164df522c133029df6d1258561f6a1a4d1f3c015`
  (Alias: `flexygram-release`, CN: `FlexyGram Release Key`)

---

## 2. Reglas Críticas para Agentes de IA (Codex, ChatGPT, etc.)

1. **POLÍTICA DE RAMAS (OBLIGATORIO):**
   - **TODA nueva función, arreglo o cambio DEBE originarse y enviarse a `codex/flexygram-beta-glass`.**
   - **NUNCA** construyas ni tomes como base ramas antiguas o desactualizadas (`main`, `alpha/...`, `ci/...`).
   - La rama canónica donde reside el 100% de los desarrollos recientes de interfaz, cabeceras, burbujas y composer es `codex/flexygram-beta-glass`.

2. **POLÍTICA DE COMPILACIÓN (NO COMPILAR EN EL CHAT):**
   - FlexyGram contiene más de 1.5 millones de líneas de código Java y pesadas librerías nativas C++ (FFmpeg, WebRTC, Chaquopy Python runtime).
   - **NO intentes compilar la APK dentro del contenedor o sandbox de un chat.**
   - La compilación se ejecuta de forma automática en **GitHub Actions** a través del flujo:
     `.github/workflows/ui-beta-debug.yml`
   - El workflow se activa automáticamente ante cada `push` a la rama `codex/flexygram-beta-glass`.

3. **CREDENCIALES Y SECRETOS:**
   - `TELEGRAM_APP_ID`, `TELEGRAM_APP_HASH` y las credenciales de Firebase ya están inyectadas de forma segura y privada como **GitHub Secrets** en el repositorio.
   - Si no se configuran, el workflow genera automáticamente un mock funcional para depuración (`flexygram-debug`).
   - **NUNCA pidas al usuario que suba su almacén de claves `.p12` ni contraseñas a una ventana de chat.**

4. **FIRMA OFICIAL DE LA APK:**
   - La firma de producción se realiza localmente en el dispositivo del propietario con su clave de custodia (`FlexyGramSigning/flexygram-release.p12`) mediante `apksigner`.
   - Las IAs se encargan del código y los tests; la custodia de la firma permanece siempre privada del usuario.

---

## 3. Mapa de Arquitectura del Repositorio

```text
FlexyGram/
├── TMessagesProj/src/main/
│   ├── java/
│   │   ├── app/flexygram/                   # Módulos exclusivos de FlexyGram
│   │   │   ├── bubbles/                     # Animaciones y física de burbujas
│   │   │   ├── composer/                    # Composer flotante, expandible y estilos
│   │   │   ├── header/                      # Cabeceras líquidas (Liquid/Signature)
│   │   │   └── icons/                       # Control de vectores e iconos iOS
│   │   └── org/telegram/ui/                 # Actividades y vistas de Telegram adaptadas
│   │       ├── ChatActivity.java            # Manejo de cabecera, menú 3 puntos y llamadas
│   │       └── Components/                  # Componentes de entrada, avatares, etc.
│   └── res/                                 # Recursos visuales
│       └── drawable/                        # Vectores (flexy_composer_*.xml, flexy_ios_back.xml)
├── .github/workflows/
│   └── ui-beta-debug.yml                    # Flujo oficial de compilación y tests ARM64
├── tools/                                   # Utilidades de verificación, Chaquopy y firmas
├── tests/                                   # Suite de pruebas automatizadas (Python y JVM)
├── docs/                                    # Documentación técnica de cambios y UI
└── gradle.properties                        # Versiones: BETA_VERSION_NAME y BETA_VERSION_CODE
```

---

## 4. Flujo de Trabajo para Nuevas Modificaciones

1. Asegúrate de tener la rama actualizada:
   ```bash
   git checkout codex/flexygram-beta-glass
   git pull origin codex/flexygram-beta-glass
   ```
2. Realiza las modificaciones de código requeridas.
3. Si cambias la versión, incrementa `BETA_VERSION_NAME` y `BETA_VERSION_CODE` en `gradle.properties`.
4. Ejecuta los tests de regresión pertinentes en `tests/`.
5. Haz commit con mensaje descriptivo y haz `push` a `codex/flexygram-beta-glass`.
6. Monitorea el flujo en GitHub Actions:
   `gh run list --branch codex/flexygram-beta-glass --limit 1`
