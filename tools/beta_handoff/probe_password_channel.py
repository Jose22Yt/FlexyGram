#!/usr/bin/env python3
"""NON-SECRET stdin transport probe only. No key, keystore, signing or network."""
import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import tempfile

FIXTURE = 'NONSECRET_FLEXYGRAM_PIPE_PROBE_V1'
SOURCE = '''import java.io.*;
class InputProbe {
  public static void main(String[] args) throws Exception {
    String line = new BufferedReader(new InputStreamReader(System.in)).readLine();
    boolean ok = "NONSECRET_FLEXYGRAM_PIPE_PROBE_V1".equals(line);
    if (!ok || System.console() != null) System.exit(2);
    System.out.println("NONSECRET_PIPE_OK");
  }
}
'''


def disable_core():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def probe(java):
    java = java.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix='flexygram-public-input-probe-') as folder:
        source = Path(folder)/'InputProbe.java'
        source.write_text(SOURCE)
        argv = [str(java), str(source)]
        env = {'PATH': os.defpath, 'LANG': 'C.UTF-8'}
        result = subprocess.run(argv, input=FIXTURE+'\n', text=True,
            capture_output=True, timeout=60, check=True, env=env,
            preexec_fn=disable_core)
        if result.stdout.strip() != 'NONSECRET_PIPE_OK' or result.stderr:
            raise ValueError('PUBLIC_INPUT_PROBE_FAILED')
        if any(FIXTURE in a for a in argv) or any(FIXTURE in v for v in env.values()):
            raise ValueError('PUBLIC_INPUT_PROBE_ARGUMENT_LEAK')
    return dict(status='NONSECRET_JAVA_STDIN_PIPE_VERIFIED', core_dumps_disabled=True,
                fixture_not_in_argv_or_environment=True, secret_generated=False,
                keytool_keystore_operation_executed=False,
                signing_executed=False, persistent_custody_verified=False,
                limits='Tests stdin transport to Java only; not protection against host administrator, memory inspection or JVM crash artifacts.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--java', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = probe(args.java)
    except Exception as error:
        print(json.dumps({'status':'BLOCKED', 'error_type':type(error).__name__}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
