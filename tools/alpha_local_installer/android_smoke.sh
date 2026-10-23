#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export ANDROID_USER_HOME="$RUNNER_TEMP/alpha-helper-android"
export ANDROID_EMULATOR_HOME="$ANDROID_USER_HOME"
export ANDROID_AVD_HOME="$ANDROID_USER_HOME/avd"
mkdir -p "$ANDROID_AVD_HOME"
sdkmanager 'platform-tools' 'emulator' 'system-images;android-35;google_apis;x86_64' > build/emulator-setup.txt
sudo chown "$(id -un)" /dev/kvm
printf 'no\n' | avdmanager create avd --force -n alpha-helper-test -p "$ANDROID_AVD_HOME/alpha-helper-test.avd" -k 'system-images;android-35;google_apis;x86_64' > build/avd-setup.txt
test -s "$ANDROID_AVD_HOME/alpha-helper-test.ini"
"$ANDROID_HOME/emulator/emulator" -list-avds
"$ANDROID_HOME/emulator/emulator" -avd alpha-helper-test -no-window -no-audio -no-boot-anim -no-snapshot -gpu swiftshader_indirect > build/emulator.txt 2>&1 &
emulator_pid=$!
cleanup() {
  result=$?
  if [[ "$result" != 0 ]]; then
    tail -n 100 build/emulator.txt || true
    adb devices -l || true
  fi
  kill "$emulator_pid" 2>/dev/null || true
  exit "$result"
}
trap cleanup EXIT
export PATH="$ANDROID_HOME/platform-tools:$PATH"
adb start-server
connected=false
for attempt in $(seq 1 90); do
  if ! kill -0 "$emulator_pid" 2>/dev/null; then echo 'Emulator exited before connecting'; exit 1; fi
  if adb devices | grep -Eq '^emulator-[0-9]+[[:space:]]+device$'; then connected=true; break; fi
  sleep 2
done
[[ "$connected" == true ]]
booted=false
for attempt in $(seq 1 120); do
  if [[ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" == '1' ]]; then booted=true; break; fi
  sleep 2
done
[[ "$booted" == true ]]
adb shell input keyevent 82
adb install -r build/FlexyGram-Alpha2-Signature-Fix-Instalador.apk
adb install -r -t build/smoke.apk
adb shell am instrument -w -r io.github.jose22yt.flexygram.delivery.alpha2.signature.tests/io.github.jose22yt.flexygram.delivery.alpha2.signature.SmokeInstrumentation | tee build/android-smoke.txt
grep -q 'helper_smoke=PASS' build/android-smoke.txt
python3 - <<'PY'
import json
from pathlib import Path
p=Path('build/helper-verification.json')
r=json.loads(p.read_text())
r['android_helper_emulator_smoke']='PASS (API 35 x86_64 helper only)'
r['physical_android_test']='NOT_TESTED'
p.write_text(json.dumps(r,indent=2)+'\n')
PY
