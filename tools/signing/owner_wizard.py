#!/usr/bin/env python3
"""Interactive owner-only custody wizard. No networking, APK handling or secret logging."""
import argparse
from datetime import datetime, timezone
from contextlib import contextmanager
import getpass
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import warnings

OFFICIAL_SHA256 = '5a598fb5ba42949b67b7c2635106fafd5f23179397e4c098757a73cd2d2ef66c'
ALIAS = 'flexygram-release'
PACKAGE = 'com.flexygram.messenger'
PASSWORD_ENV = 'FLEXYGRAM_LOCAL_STORE_PASSWORD'
VERIFIER = Path(__file__).resolve().with_name('VerifySigning.java')


class CustodyError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise CustodyError(message)


def runtime_preflight():
    require(sys.stdin.isatty() and sys.stderr.isatty(), 'Ejecuta el asistente en una terminal interactiva propia, sin tuberías.')
    hosted = ['GITHUB_ACTIONS', 'CI', 'CODEX_PRIMARY_RUNTIME_ROOT', 'CODEX_HOME']
    require(not any(os.environ.get(key) for key in hosted), 'No se permite generar identidades en CI ni en la sesión del asistente.')
    for tool in ('java', 'keytool', 'age'):
        require(shutil.which(tool) is not None, 'Falta una herramienta: ' + tool + '. Consulta README_LOCAL.md.')
    require(VERIFIER.is_file(), 'Falta VerifySigning.java del mismo paquete de herramientas.')
    version = subprocess.run(['java', '-version'], capture_output=True, text=True)
    match = re.search(r'version "(\d+)', version.stdout + version.stderr)
    require(version.returncode == 0 and match and int(match[1]) >= 17, 'Se requiere JDK 17 o posterior; el proyecto prevé JDK 21.')


def vault_path(value):
    path = Path(value).expanduser()
    require(not path.is_symlink(), 'La carpeta del original no puede ser un enlace simbólico.')
    resolved = path.resolve()
    home = Path.home().resolve()
    require(resolved != home and home in resolved.parents, 'Guarda el original dentro de una carpeta privada de tu directorio personal.')
    shared_roots = ('/storage/', '/sdcard/', '/mnt/', '/tmp/', '/var/tmp/')
    require(not str(resolved).startswith(shared_roots), 'El original no puede estar en almacenamiento compartido, externo o temporal.')
    require(not any((parent / '.git').exists() for parent in [resolved, *resolved.parents]), 'El original debe quedar fuera de todo repositorio Git.')
    return resolved


def prepare_vault(path):
    if not path.exists():
        path.mkdir(mode=0o700, parents=False)
    require(path.is_dir(), 'La ubicación privada debe ser una carpeta.')
    if os.name == 'posix':
        info = path.stat()
        require(info.st_uid == os.getuid(), 'La carpeta privada debe ser de tu usuario.')
        require(stat.S_IMODE(info.st_mode) & 0o077 == 0, 'La carpeta privada requiere permisos 700; no se corrigen automáticamente carpetas ajenas.')


@contextmanager
def locked(vault):
    lock = vault / '.owner-custody.lock'
    fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.close(fd)
        yield
    finally:
        lock.unlink(missing_ok=True)


def write_state(vault, data):
    state = vault / 'custody-state.json'
    require(not state.is_symlink(), 'El registro de custodia no puede ser un enlace.')
    fd, name = tempfile.mkstemp(prefix='.state-', dir=vault)
    try:
        with os.fdopen(fd, 'w') as output:
            json.dump(data, output, indent=2)
            output.write('\n')
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, state)
    finally:
        Path(name).unlink(missing_ok=True)


def load_state(vault):
    path = vault / 'custody-state.json'
    require(not path.is_symlink(), 'Registro de custodia inválido.')
    if not path.exists():
        return {'package': PACKAGE, 'alias': ALIAS, 'status': 'PENDING', 'backups': []}
    try:
        state = json.loads(path.read_text())
    except (ValueError, OSError):
        raise CustodyError('Registro ilegible: conserva la clave existente; no la regeneres.') from None
    require(state.get('package') == PACKAGE and state.get('alias') == ALIAS, 'Registro de otra identidad: no se sustituye.')
    fingerprint = state.get('sha256')
    require(fingerprint is None or re.fullmatch(r'[a-f0-9]{64}', fingerprint), 'Huella local inválida: no se sustituye.')
    return state


def ask_password(confirm=False):
    print('Usa una contraseña exclusiva de al menos 32 caracteres aleatorios, guardada en tu gestor. No se mostrará.')
    with warnings.catch_warnings():
        warnings.simplefilter('error', getpass.GetPassWarning)
        password = getpass.getpass('Contraseña PKCS12: ')
        require(len(password) >= 32 and all(33 <= ord(c) <= 126 for c in password), 'Usa al menos 32 caracteres ASCII imprimibles sin espacios, generados por tu gestor.')
        if confirm:
            require(hmac.compare_digest(password, getpass.getpass('Repite la contraseña PKCS12: ')), 'Las contraseñas no coinciden.')
    return password


def private_command(command, password):
    env = dict(os.environ)
    env[PASSWORD_ENV] = password
    try:
        result = subprocess.run(command, env=env, capture_output=True, text=True)
    finally:
        env.pop(PASSWORD_ENV, None)
    require(result.returncode == 0, 'Falló una herramienta privada. Conserva el original; no se vuelcan contraseñas, entradas ni errores del proveedor.')
    return result.stdout


def inspect(store, password, expected=None):
    command = ['java', str(VERIFIER), 'keystore-env', str(store)]
    if expected:
        command.append(expected)
    report = json.loads(private_command(command, password))
    require(report.get('status') == 'PASS' and report.get('private_key') == 'POSSESSION_VERIFIED', 'No se acreditó acceso a la clave privada.')
    require(re.fullmatch(r'[a-f0-9]{64}', report.get('sha256', '')), 'El verificador no devolvió una huella pública válida.')
    require(hmac.compare_digest(report['sha256'], OFFICIAL_SHA256), 'La clave no corresponde a la identidad oficial registrada.')
    require(expected is None or hmac.compare_digest(report['sha256'], expected), 'La identidad difiere de la huella fijada.')
    return report


def create_or_resume(vault, password, state):
    store = vault / 'flexygram-release.p12'
    require(not store.is_symlink(), 'No se admite un enlace como almacén privado.')
    require(store.is_file(), 'La identidad oficial ya existe. Recupera tu PKCS12 original en esta carpeta; no se permite generar otra clave.')
    require(state.get('sha256') in (None, OFFICIAL_SHA256), 'El registro local corresponde a otra identidad; no se sustituye.')
    print('Se verificará el original oficial; este asistente ya no genera claves.')
    report = inspect(store, password, OFFICIAL_SHA256)
    state.update(sha256=report['sha256'], status='KEY_VERIFIED_BACKUPS_PENDING')
    write_state(vault, state)
    cert = vault / 'flexygram-release.cer'
    require(not cert.is_symlink(), 'El certificado público no puede ser un enlace.')
    if not cert.exists():
        private_command(['keytool', '-exportcert', '-keystore', str(store), '-storetype', 'PKCS12',
                         '-alias', ALIAS, '-file', str(cert), '-storepass:env', PASSWORD_ENV], password)
    result = subprocess.run(['java', str(VERIFIER), 'certificate', str(cert), report['sha256']], capture_output=True, text=True)
    require(result.returncode == 0, 'El certificado público no coincide; conserva el original.')
    return store, report


def backup_target(text, vault, previous):
    require(bool(text), 'Debes indicar la ruta de un archivo cifrado .age.')
    raw = Path(text).expanduser()
    require(not raw.is_symlink(), 'No se admite un enlace como backup.')
    path = raw.resolve()
    require(path.suffix == '.age', 'La copia cifrada debe terminar en .age.')
    require(path.parent.is_dir(), 'La carpeta de destino debe existir y estar accesible.')
    require(vault not in [path, *path.parents], 'El backup final debe estar fuera de la carpeta del original.')
    require(not path.is_symlink(), 'No se admite un enlace como backup.')
    require(path not in previous and all(path.parent != p.parent for p in previous), 'A y B requieren ubicaciones distintas; dos nombres en la misma carpeta no son dos soportes.')
    return path


def encrypt_new(store, target):
    # Exclusive creation prevents silent replacement of an existing backup.
    with target.open('xb') as output:
        try:
            print('age pedirá una contraseña de backup: usa una frase fuerte del gestor, distinta del PKCS12 y guárdala.')
            result = subprocess.run(['age', '-p', str(store)], stdout=output)
            output.flush()
            os.fsync(output.fileno())
            require(result.returncode == 0, 'No terminó el cifrado; el original se conserva.')
        except BaseException:
            target.unlink(missing_ok=True)
            raise


def file_digest(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(65536), b''):
            digest.update(chunk)
    return digest.digest()


def restore_and_verify(store, target, password, fingerprint, vault):
    # All temporary plaintext remains within the private, encrypted-device vault.
    with tempfile.TemporaryDirectory(prefix='.recovery-', dir=vault) as directory:
        recovered = Path(directory) / 'recovered.p12'
        with recovered.open('xb') as output:
            result = subprocess.run(['age', '-d', str(target)], stdout=output)
        require(result.returncode == 0, 'El backup no pudo descifrarse; no se confirma custodia.')
        require(hmac.compare_digest(file_digest(store), file_digest(recovered)), 'El archivo recuperado difiere del original.')
        inspect(recovered, password, fingerprint)


def run_setup(vault):
    state = load_state(vault)
    if state.get('sha256'):
        state['status'] = 'REVALIDATION_PENDING'
        write_state(vault, state)
    print('El original quedará en la carpeta privada elegida. No desinstales la terminal ni borres sus datos.')
    print('Necesitas dos destinos finales separados. Dos carpetas del mismo teléfono NO son dos soportes independientes.')
    targets = []
    for label in ('A', 'B'):
        target = backup_target(input('Ruta del archivo .age en el soporte final ' + label + ': ').strip(), vault, targets)
        targets.append(target)
    require((vault / 'flexygram-release.p12').is_file(), 'Recupera el PKCS12 oficial antes de continuar; no se generan nuevas identidades.')
    password = ask_password(confirm=False)
    try:
        store, report = create_or_resume(vault, password, state)
        state['backups'] = []
        write_state(vault, state)
        for label, target in zip(('A', 'B'), targets):
            if target.exists():
                print('Existe un backup en ese destino: solo se verificará, nunca se sobrescribe.')
            else:
                encrypt_new(store, target)
            print('Recuperando y comprobando copia ' + label + ' desde su ubicación final…')
            restore_and_verify(store, target, password, report['sha256'], vault)
            state['backups'].append({'label': label, 'location': str(target), 'restoration_verified': True})
            write_state(vault, state)
        print('Ambas rutas se han restaurado y la clave coincide. El software no puede comprobar su independencia física.')
        print('Confirma solo si A/B están en soportes independientes y puedes recuperar las contraseñas fuera del dispositivo original.')
        confirmation = input('Escribe CONFIRMO si tienes el original, las contraseñas y ambos backups independientes: ').strip()
        if confirmation != 'CONFIRMO':
            state['status'] = 'TWO_RESTORES_VERIFIED_OWNER_CONFIRMATION_PENDING'
            write_state(vault, state)
            print('PENDIENTE: no se ha confirmado custodia independiente. El original permanece intacto.')
            return 2
        state['status'] = 'OWNER_ATTESTED_AFTER_TWO_RESTORES'
        write_state(vault, state)
        public = {key: report[key] for key in ['sha256', 'public_key', 'signature', 'not_before', 'not_after']}
        public.update(package=PACKAGE, alias=ALIAS, custody=state['status'], private_key='POSSESSION_VERIFIED', android_apk='NOT_TESTED')
        public['verified_at_utc'] = datetime.now(timezone.utc).isoformat()
        fd, name = tempfile.mkstemp(prefix='.public-report-', dir=vault)
        try:
            with os.fdopen(fd, 'w') as output:
                json.dump(public, output, indent=2)
                output.write('\n')
                output.flush()
                os.fsync(output.fileno())
            os.replace(name, vault / 'public-verification.json')
        finally:
            Path(name).unlink(missing_ok=True)
        print('Comprobación local terminada y custodia declarada por el propietario.')
        print('SHA-256 pública: ' + report['sha256'])
        print('Para revisión comparte SOLO flexygram-release.cer y public-verification.json. Nunca el .p12, .age o contraseñas.')
        return 0
    finally:
        password = None  # Python cannot guarantee erasure of all in-memory string copies.


def main():
    parser = argparse.ArgumentParser(description='Asistente LOCAL de recuperación y custodia de la firma oficial de FlexyGram. No genera claves ni APK.')
    parser.add_argument('--vault', default=str(Path.home() / 'FlexyGramSigning'))
    parser.add_argument('--status', action='store_true', help='Muestra solo el estado público local; no abre ni genera claves')
    args = parser.parse_args()
    os.umask(0o077)
    vault = None
    try:
        vault = vault_path(args.vault)
        if args.status:
            state = load_state(vault)
            print(json.dumps({key: state.get(key) for key in ['package', 'alias', 'status', 'sha256']}, indent=2))
            return 0
        runtime_preflight()
        prepare_vault(vault)
        with locked(vault):
            return run_setup(vault)
    except CustodyError as error:
        print('PENDIENTE: ' + str(error), file=sys.stderr)
        print('No se confirma custodia ni se reemplaza una clave existente.', file=sys.stderr)
        return 1
    except (OSError, ValueError, EOFError, KeyboardInterrupt, getpass.GetPassWarning):
        # No raw provider exceptions, entered paths, passwords, tracebacks or key encodings.
        print('PENDIENTE: el procedimiento no terminó. No se confirma custodia ni se regenera una clave existente.', file=sys.stderr)
        if vault and (vault / 'flexygram-release.p12').exists():
            print('El original existente se conserva. Corrige el problema y vuelve a ejecutar el asistente.', file=sys.stderr)
        else:
            print('Revisa terminal propia, herramientas, carpeta privada, destinos de backups y entradas. Consulta README_LOCAL.md.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
