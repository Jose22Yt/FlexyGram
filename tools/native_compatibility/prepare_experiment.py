"""Prepare a disposable checkout build overlay, never the source checkout itself.
The approved diagnostic requirements/lock/build file are not changed.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess

def replace_python_preparation(text, replacement):
 # Replace only the reviewed task/wiring, retaining later overlays and gates.
 start_marker='// P0.4c: pip resolves exclusively'
 end_marker="""tasks.configureEach { task ->
    if (task.name.startsWith('install') && task.name.endsWith('PythonRequirements')) {
        task.dependsOn(prepareLockedPython)
    }
}"""
 if text.count(start_marker)!=1 or text.count(end_marker)!=1:
  raise ValueError('Reviewed Python preparation block no longer matches')
 start=text.index(start_marker);end=text.index(end_marker)+len(end_marker)
 if end<=start:raise ValueError('Reviewed Python preparation block is out of order')
 return text[:start]+replacement+text[end:]

def unsigned_diagnostic(text):
 old='signingConfig = signingConfigs.diagnosticLab'
 if text.count(old)!=1:raise ValueError('Reviewed diagnostic signing assignment no longer matches')
 return text.replace(old,'// Experimental unsigned artifact: no flavor signing assignment or key access')

def overlay(source,checkout,wheelhouse,manifest,python,unsigned=False):
 source=source.resolve();checkout=checkout.resolve();wheelhouse=wheelhouse.resolve();manifest=manifest.resolve()
 if source==checkout or source in checkout.parents:raise ValueError('Use independent disposable checkout')
 src=source/'TMessagesProj/build.gradle';dst=checkout/'TMessagesProj/build.gradle'
 if dst.read_bytes()!=src.read_bytes():raise ValueError('Experimental checkout is not the approved build configuration')
 # Pip inputs and offline materialization change only in this checkout. The
 # optional unsigned overlay removes diagnostic signing, never adding a key.
 # Variant policy, manifest, sources, JNI and capability code remain identical.
 requirements=manifest.with_name('requirements-experimental.lock')
 lock=json.loads((source/'TMessagesProj/python/wheels.lock.json').read_text());rows=json.loads(manifest.read_text())['wheels']
 byoriginal={r['original_filename']:r for r in rows};lines=['# Experimental ARM64 only. Not an active diagnostic lock.']
 for package in lock['packages']:
  selected=[byoriginal[f['filename']] for f in package['files'] if f['filename'] in byoriginal]
  if len(selected)!=1:raise ValueError('Experimental selection must contain one wheel per package')
  lines.append(package['name']+'=='+package['version']+' --hash=sha256:'+selected[0]['sha256'])
 requirements.write_text('\n'.join(lines)+'\n')
 text=src.read_text()
 if unsigned:text=unsigned_diagnostic(text)
 for old,new in [("file('build/locked-wheelhouse').absolutePath",repr(str(wheelhouse))),
  ("file('python/requirements.lock').absolutePath",repr(str(requirements)))]:
  if text.count(old)!=(2 if 'wheelhouse' in old else 1):raise ValueError('Reviewed build overlay no longer matches')
  text=text.replace(old,new)
 text=replace_python_preparation(text,'''// Isolated 16 KB experiment: validate exact local wheels before pip.
 def prepareLockedPython = tasks.register('prepareLockedPython', Exec) {
     commandLine '''+repr(str(python))+', '+repr(str(source/'tools/native_compatibility/experimental_wheels.py'))+", 'verify', '--manifest', "+repr(str(manifest))+", '--wheelhouse', "+repr(str(wheelhouse))+'''
 }
 tasks.configureEach { task ->
     if (task.name.startsWith('install') && task.name.endsWith('PythonRequirements')) task.dependsOn(prepareLockedPython)
 }
''')
 dst.write_text(text)
 return {'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),
  'approved_build_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'overlay_build_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),
  'experimental_manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'production_and_policy_unchanged':True,
  'unsigned_diagnostic':unsigned}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['source','checkout','wheelhouse','manifest','python']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--unsigned',action='store_true',help='Remove only the diagnostic signing assignment in the disposable checkout')
 a=p.parse_args();print(json.dumps(overlay(a.source,a.checkout,a.wheelhouse,a.manifest,a.python,a.unsigned),indent=2))
