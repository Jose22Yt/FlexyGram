"""Source-link compatibility bridge for the pinned GNU-era libraries.
Never patches an ELF. Never omits an export from the acceptance oracle.
Only known absolute metadata is reconstructed; function objects stay untouched.
"""
from pathlib import Path
from io import BytesIO
import re,shlex,subprocess
from elftools.elf.elffile import ELFFile
from audit import elf,versions
from acceptance import candidate_contract

BOUNDARIES={'__bss_start':'ADDR(.bss)','__bss_start__':'ADDR(.bss)',
 '_edata':'ADDR(.data)+SIZEOF(.data)','__bss_end__':'ADDR(.bss)+SIZEOF(.bss)',
 '_bss_end__':'ADDR(.bss)+SIZEOF(.bss)','__end__':'ADDR(.bss)+SIZEOF(.bss)',
 '_end':'ADDR(.bss)+SIZEOF(.bss)'}

def metadata_nodes(data):
 e=ELFFile(BytesIO(data));_,defs=versions(e);nodes=[]
 for s in e.get_section_by_name('.dynsym').iter_symbols():
  if s.name in defs.values():
   if s['st_info']['type']!='STT_OBJECT' or s['st_shndx']!='SHN_ABS' or s['st_value'] or s['st_size']:
    raise ValueError('Unsupported version-node metadata')
   nodes.append(s.name)
 return sorted(set(nodes))

def version_map(text,nodes):
 for n in nodes:
  pattern=r'('+re.escape(n)+r'\s*\{\s*global:)'
  text,count=re.subn(pattern,lambda m:m[1]+'\n  '+n+';',text)
  if count!=1:raise ValueError('Version node absent/ambiguous in source map: '+n)
 return text

def link_args(line,obj,script,trim_transitive_zlib):
 args=shlex.split(line)
 if '-shared' not in args or '-o' not in args:raise ValueError('Not a shared link recipe')
 i=args.index('-o');args[i:i]=[str(obj),'-Wl,-T,'+str(script)]
 # Apply as-needed only to libz, whose original contracts use the libxml2 edge.
 # Do not change any other library edge, or drop any object/archive.
 if trim_transitive_zlib:
  if args.count('-lz')!=1:raise ValueError('Unexpected zlib dependency shape')
  i=args.index('-lz');args[i:i+1]=['-Wl,--as-needed','-lz','-Wl,--no-as-needed']
 return args

def relink(output,ndk,originals,linker=None,stubs=None):
 tool=ndk/'toolchains/llvm/prebuilt/linux-x86_64/bin';rows=[]
 for name,sub,base,mapname in [('libxml2.so','libxml2-2.9.8','','libxml2.syms'),
   ('libxslt.so','libxslt-1.1.32','libxslt','libxslt.syms'),
   ('libexslt.so','libxslt-1.1.32','libexslt',None)]:
  directory=output/'sources'/sub/base;nodes=metadata_nodes(originals[name])
  obj=directory/'compat-nodes.o';asm=directory/'compat-nodes.s';script=directory/'compat-boundaries.ld'
  asm.write_text('\n'.join(f'.globl {n}\n.type {n}, %object\n.set {n}, 0' for n in nodes)+'\n')
  subprocess.run([str(tool/'aarch64-linux-android24-clang'),'-c',str(asm),'-o',str(obj)],check=True)
  if mapname and linker is None:
   p=directory/mapname;p.write_text(version_map(p.read_text(),nodes))
  # ABSOLUTE matches the original STT_NOTYPE/SHN_ABS contract; values follow the
  # actual new BSS layout rather than copying obsolete original addresses.
  script.write_text('SECTIONS { .compat_boundary : { } } INSERT AFTER .bss;\n'+
   ''.join(f'{n} = ABSOLUTE({v});\n' for n,v in BOUNDARIES.items() if any(x[0]==n for x in elf(originals[name],name)['exports'])))
  log=(output/(sub+'.log')).read_text()
  links=[line.removeprefix('libtool: link: ') for line in log.splitlines()
    if line.startswith('libtool: link: ') and ' -shared ' in line and re.search(r'-o \.libs/'+re.escape(name)+r'(?: |$)',line)]
  if len(links)!=1:raise ValueError('Expected exactly one recorded source link for '+name)
  args=link_args(links[0],obj,script,name!='libxml2.so')
  if linker is not None:
   # GNU emits the absolute version-node objects AND parent chains itself.
   args.remove(str(obj))
   args[1:1]=['-fuse-ld='+str(linker),'-L'+str(stubs),'-Wl,--hash-style=both']
   if name!='libxml2.so':
    # Preserve original DT_NEEDED ordering as well as its exact set.
    xml_inputs=[i for i,x in enumerate(args) if x.endswith('/libxml2.so')]
    if len(xml_inputs)!=1:raise ValueError('Expected one direct XML link input')
    args.insert(xml_inputs[0],'-lm')
  with (output/(name+'.compat-link.log')).open('w') as stream:
   subprocess.run(args,cwd=directory,stdout=stream,stderr=subprocess.STDOUT,check=True)
  candidate=directory/'.libs'/name
  # Subsequent XSLT links consume the compatible XML built here, not a host lib.
  (output/'prefix/lib'/name).write_bytes(candidate.read_bytes())
  contract=candidate_contract(elf(originals[name],name),elf(candidate.read_bytes(),name))
  if not contract['static_contract_pass']:raise ValueError('Compatibility contract blocked: '+str(contract))
  rows.append({'library':name,'nodes':nodes,'args':args,'contract':contract})
 return rows
