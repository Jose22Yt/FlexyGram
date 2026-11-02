"""Link actual pinned AAR resources and generate their R classes, as AGP normally does.
No replacements for RecyclerView/core implementations or hand-written resource constants.
"""
from pathlib import Path
import subprocess,zipfile

def link_resources(output,repository,sdk):
 aapt=sdk/'build-tools/36.0.0/aapt2'
 command=[str(aapt),'link','-I',str(sdk/'platforms/android-37.0/android.jar'),'--manifest',str(output/'AndroidManifest.xml'),
          '--auto-add-overlay','--java',str(output/'src/test/java'),'--extra-packages','androidx.core:androidx.recyclerview:androidx.customview:androidx.customview.poolingcontainer',
          '-o',str(output/'resources.ap_'),str(output/'resources.zip')]
 for group,artifact,version in [('androidx.core','core','1.17.0'),('androidx.recyclerview','recyclerview','1.4.0'),('androidx.customview','customview','1.0.0'),('androidx.customview','customview-poolingcontainer','1.0.0')]:
  aar=repository/group.replace('.','/')/artifact/version/(artifact+'-'+version+'.aar')
  folder=output/'target/aar-res'/artifact;folder.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(aar) as z:
   for name in z.namelist():
    path=Path(name)
    if name.startswith('res/') and not name.endswith('/') and '..' not in path.parts:
     dest=folder/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
  if not (folder/'res').is_dir(): continue
  compiled=folder/'compiled.zip'
  subprocess.run([str(aapt),'compile','--dir',str(folder/'res'),'-o',str(compiled)],check=True)
  command+=['-R',str(compiled)]
 subprocess.run(command,check=True)
