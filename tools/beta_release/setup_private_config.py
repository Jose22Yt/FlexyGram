#!/usr/bin/env python3
"""
Asistente interactivo privado para configurar credenciales y firma de FlexyGram Beta.
No imprime contraseñas en pantalla ni las envía por la red.
Guarda la configuración exclusivamente en local.properties (ignorado por git).
"""
import getpass
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_SHA256 = 'e71c4d1e14dd940892009c61164df522c133029df6d1258561f6a1a4d1f3c015'
DEFAULT_KEYSTORE = Path.home() / 'FlexyGramSigning/flexygram-release.p12'
OFFICIAL_ALIAS = 'flexygram-release'
APP_PACKAGE = 'com.flexygram.messenger'
TARGET_GOOGLE_SERVICES = ROOT / 'TMessagesProj/src/beta/google-services.json'


def test_keystore_password(keystore_path, password, alias):
    """Verifica la contraseña contra keytool sin registrarla en logs."""
    try:
        proc = subprocess.run(
            ['keytool', '-list', '-keystore', str(keystore_path),
             '-storetype', 'PKCS12', '-alias', alias],
            input=password.encode('utf-8') + b'\n',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
        if proc.returncode != 0:
            return False, "La contraseña no abre el almacén o el alias 'flexygram-release' no existe."
        # Extraer SHA256 si está presente en la salida de keytool
        output = proc.stdout.decode('utf-8', errors='ignore')
        sha_match = re.search(r'SHA256:\s*([0-9A-Fa-f:]+)', output)
        if sha_match:
            sha_found = sha_match.group(1).replace(':', '').lower()
            if sha_found != OFFICIAL_SHA256:
                return False, f"La huella de la clave ({sha_found}) NO coincide con la firma oficial ({OFFICIAL_SHA256})."
        return True, "Firma y contraseña verificadas con éxito."
    except FileNotFoundError:
        # Si keytool no está disponible directamente en PATH, permitir continuar con advertencia
        return True, "keytool no disponible para verificación previa; se validará durante la compilación."


def main():
    print("=" * 65)
    print("  Configuración Privada de FlexyGram Beta")
    print("=" * 65)
    print("Este script configura de forma segura y privada tu entorno local.")
    print("Las contraseñas NO se mostrarán en pantalla ni se subirán a GitHub.\n")

    # 1. Keystore
    print("[1/4] Archivo de Firma (.p12)")
    keystore_path_str = input(f"Ruta del archivo .p12 [{DEFAULT_KEYSTORE}]: ").strip()
    if not keystore_path_str:
        keystore_path = DEFAULT_KEYSTORE
    else:
        keystore_path = Path(keystore_path_str).expanduser().resolve()

    if not keystore_path.is_file():
        print(f"❌ Error: El archivo '{keystore_path}' no existe.")
        sys.exit(1)

    try:
        if keystore_path.is_relative_to(ROOT.resolve()):
            print("❌ Error de seguridad: El keystore debe estar FUERA del repositorio.")
            sys.exit(1)
    except AttributeError:
        # En Python anterior a 3.9
        pass

    print(f"✔ Archivo de firma encontrado: {keystore_path}")

    # 2. Contraseñas
    print("\n[2/4] Contraseñas del almacén y clave")
    store_password = getpass.getpass("Introduce la contraseña del almacén (.p12) [oculta]: ")
    if not store_password:
        print("❌ Error: La contraseña no puede estar vacía.")
        sys.exit(1)

    # Validar contraseña si es posible
    valid, msg = test_keystore_password(keystore_path, store_password, OFFICIAL_ALIAS)
    if not valid:
        print(f"❌ Error al validar contraseña: {msg}")
        reintentar = input("¿Deseas guardar de todos modos? (s/N): ").strip().lower()
        if reintentar != 's':
            sys.exit(1)
    else:
        print(f"✔ {msg}")

    key_password = getpass.getpass(f"Contraseña de la clave 'flexygram-release' (Enter para misma que almacén): ")
    if not key_password:
        key_password = store_password

    # 3. Credenciales Telegram
    print("\n[3/4] Credenciales de Telegram (de https://my.telegram.org)")
    app_id = input("TELEGRAM_APP_ID (número entero): ").strip()
    if not re.fullmatch(r'[1-9][0-9]{0,9}', app_id) or int(app_id) > 2147483647 or app_id in ['4', '6', '2040']:
        print("❌ Error: TELEGRAM_APP_ID inválido o reservado.")
        sys.exit(1)

    app_hash = input("TELEGRAM_APP_HASH (32 caracteres hexadecimales): ").strip()
    if not re.fullmatch(r'[a-fA-F0-9]{32}', app_hash):
        print("❌ Error: TELEGRAM_APP_HASH debe tener 32 caracteres hexadecimales.")
        sys.exit(1)

    # 4. Firebase google-services.json
    print("\n[4/4] Archivo Firebase google-services.json")
    if TARGET_GOOGLE_SERVICES.is_file():
        try:
            cfg = json.loads(TARGET_GOOGLE_SERVICES.read_text())
            pkgs = [c.get('client_info', {}).get('android_client_info', {}).get('package_name')
                    for c in cfg.get('client', [])]
            if APP_PACKAGE in pkgs:
                print(f"✔ Archivo Firebase ya configurado en {TARGET_GOOGLE_SERVICES} para {APP_PACKAGE}.")
            else:
                print(f"⚠️ El archivo existente en {TARGET_GOOGLE_SERVICES} no contiene el paquete '{APP_PACKAGE}'.")
                TARGET_GOOGLE_SERVICES.unlink()
        except Exception:
            pass

    if not TARGET_GOOGLE_SERVICES.is_file():
        fb_path_str = input(f"Ruta de tu google-services.json (ej: /sdcard/Download/google-services.json) [Enter para omitir por ahora]: ").strip()
        if fb_path_str:
            fb_path = Path(fb_path_str).expanduser().resolve()
            if not fb_path.is_file():
                print(f"⚠️ Advertencia: No se encontró el archivo '{fb_path}'. Deberás copiarlo manualmente después a {TARGET_GOOGLE_SERVICES}.")
            else:
                try:
                    cfg = json.loads(fb_path.read_text())
                    pkgs = [c.get('client_info', {}).get('android_client_info', {}).get('package_name')
                            for c in cfg.get('client', [])]
                    if APP_PACKAGE not in pkgs:
                        print(f"❌ Error: El archivo no registra el paquete '{APP_PACKAGE}'. Paquetes encontrados: {pkgs}")
                    else:
                        TARGET_GOOGLE_SERVICES.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(fb_path, TARGET_GOOGLE_SERVICES)
                        os.chmod(TARGET_GOOGLE_SERVICES, 0o600)
                        print(f"✔ Copiado a {TARGET_GOOGLE_SERVICES} con permisos seguros.")
                except Exception as e:
                    print(f"❌ Error al leer JSON de Firebase: {e}")

    # Guardar en local.properties
    local_props_path = ROOT / 'local.properties'
    existing_props = {}
    if local_props_path.is_file():
        for line in local_props_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                existing_props[k.strip()] = v.strip()

    existing_props['FLEXYGRAM_RELEASE_KEYSTORE'] = str(keystore_path)
    existing_props['FLEXYGRAM_RELEASE_KEY_ALIAS'] = OFFICIAL_ALIAS
    existing_props['FLEXYGRAM_RELEASE_STORE_PASSWORD'] = store_password
    existing_props['FLEXYGRAM_RELEASE_KEY_PASSWORD'] = key_password
    existing_props['TELEGRAM_APP_ID'] = app_id
    existing_props['TELEGRAM_APP_HASH'] = app_hash

    lines = [
        "# Configuración Privada de FlexyGram Beta",
        "# Este archivo está protegido por .gitignore y NUNCA se sube a GitHub.",
        ""
    ]
    for k, v in existing_props.items():
        lines.append(f"{k}={v}")

    local_props_path.write_text('\n'.join(lines) + '\n')
    os.chmod(local_props_path, 0o600)
    print(f"\n✔ Configuración guardada en {local_props_path} con permisos 0600 (solo lectura de tu usuario).")

    # Ejecutar preflight
    print("\nEjecutando verificación final:")
    sys.path.insert(0, str(ROOT / 'tools/beta_release'))
    from preflight import inspect
    report = inspect(root=ROOT)
    print(json.dumps(report, indent=2))
    if report.get('status') == 'INPUTS_PRESENT_PRIVATE_VALIDATION_REQUIRED':
        print("\n🎉 ¡Todo listo! Todas las entradas privadas requeridas están configuradas.")
    else:
        print("\n⚠️ Aún faltan entradas o resolver advertencias para completar la configuración.")


if __name__ == '__main__':
    main()
