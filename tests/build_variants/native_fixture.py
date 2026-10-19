"""Generate the real CMake policy in an isolated host-only build directory."""
from pathlib import Path
import hashlib,subprocess
ROOT=Path(__file__).resolve().parents[2]
def configure(directory,flavor='diagnostic',scope=None):
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
 scope=scope or hashlib.sha256((ROOT/'gradle/variant-policy.json').read_bytes()).hexdigest()+':'+flavor
 script=directory/'CMakeLists.txt'
 script.write_text('cmake_minimum_required(VERSION 3.16)\nproject(VariantFixture NONE)\ninclude("'+str(ROOT/'TMessagesProj/jni/variant-policy.cmake')+'")\n')
 result=subprocess.run(['cmake','-DFLEXYGRAM_FLAVOR='+flavor,'-DFLEXYGRAM_POLICY_SCOPE='+scope,'-S',str(directory),'-B',str(directory/'build')],cwd=directory,capture_output=True,text=True)
 if result.returncode:raise RuntimeError(result.stdout+result.stderr)
 return directory/'build/flexygram-policy'
