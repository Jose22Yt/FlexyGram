"""Typed ABI/feature evidence; additive to the unchanged conservative gate."""
from io import BytesIO
from elftools.elf.elffile import ELFFile
from audit import elf
from acceptance import candidate_contract

def detail(data):
 e=ELFFile(BytesIO(data));symbols={}
 for s in e.get_section_by_name('.dynsym').iter_symbols():
  if s['st_shndx']!='SHN_UNDEF' and s['st_info']['bind'] in ('STB_GLOBAL','STB_WEAK') and s['st_other']['visibility'] in ('STV_DEFAULT','STV_PROTECTED'):
   symbols[s.name]={'type':s['st_info']['type'],'bind':s['st_info']['bind'],'visibility':s['st_other']['visibility'],
    'size':s['st_size'] if s['st_info']['type']=='STT_OBJECT' else None,
    'absolute':s['st_shndx']=='SHN_ABS'}
 versions={};vd=e.get_section_by_name('.gnu.version_d')
 if vd:
  for version,aux in vd.iter_versions():
   names=[a.name for a in aux];versions[names[0]]={'parents':names[1:],'flags':version['vd_flags'],'hash':version['vd_hash']}
 dynamic=e.get_section_by_name('.dynamic')
 return {'symbols':symbols,'version_definitions':versions,
  'dynamic_tags':[t.entry.d_tag for t in dynamic.iter_tags()],
  'hash_sections':[n for n in ['.hash','.gnu.hash'] if e.get_section_by_name(n)]}
def compare(before,after,name):
 a,b=detail(before),detail(after);contract=candidate_contract(elf(before,name),elf(after,name))
 typed=[{'name':n,'before':v,'after':b['symbols'].get(n)} for n,v in a['symbols'].items() if v!=b['symbols'].get(n)]
 version_diff=[n for n,v in a['version_definitions'].items() if v!=b['version_definitions'].get(n)]
 return {'library':name,'contract':contract,'typed_export_differences':typed,'version_definition_differences':version_diff,
  'new_export_names':sorted(set(b['symbols'])-set(a['symbols'])),
  'old_export_names':len(a['symbols']),'new_export_count':len(b['symbols']),
  'before_hash_sections':a['hash_sections'],'after_hash_sections':b['hash_sections'],
  'static_abi_pass':contract['static_contract_pass'] and not typed and not version_diff,
  'runtime_validated':False}
