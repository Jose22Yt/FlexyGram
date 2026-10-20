"""Read-only section/ABI/relocation comparison; never loads an ELF or signs an APK."""
from io import BytesIO
from pathlib import Path
import argparse
import hashlib
import json
import re
from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return digest(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def inspect(data):
    require(data.startswith(b'\x7fELF'), 'Not an ELF')
    elf = ELFFile(BytesIO(data))
    require(elf.elfclass == 64 and elf.little_endian, 'ELF64 little endian required')
    sections = {}
    paths = []
    relocations = []
    for section in elf.iter_sections():
        name = section.name
        require(name not in sections, 'Ambiguous section name')
        nobits = section['sh_type'] == 'SHT_NOBITS'
        require(nobits or section['sh_offset'] + section['sh_size'] <= len(data),
                'Truncated section')
        payload = b'' if nobits else section.data()
        row = {'type': section['sh_type'], 'flags': section['sh_flags'],
               'address': section['sh_addr'], 'size': section['sh_size'],
               'alignment': section['sh_addralign'],
               'sha256': None if nobits else digest(payload)}
        sections[name] = row
        for match in re.finditer(rb'/workspace/scratch/[ -~]+', payload):
            text = match.group().decode('ascii')
            paths.append({'section': name, 'section_offset': match.start(),
                          'allocated': bool(section['sh_flags'] & 2),
                          'executable': bool(section['sh_flags'] & 4),
                          'bytes': len(text), 'sha256': digest(match.group()),
                          'root': '/'.join(text.split('/')[:5])})
        if isinstance(section, RelocationSection):
            symbols = elf.get_section(section['sh_link'])
            for relocation in section.iter_relocations():
                index = relocation['r_info_sym']
                relocations.append([name, relocation['r_offset'], relocation['r_info_type'],
                                    symbols.get_symbol(index).name if index else '',
                                    relocation['r_addend'] if relocation.is_RELA() else None])
    exports = []
    symbols = elf.get_section_by_name('.dynsym')
    require(symbols is not None, 'Dynamic symbol table required')
    for symbol in symbols.iter_symbols():
        if symbol['st_shndx'] != 'SHN_UNDEF' and symbol['st_info']['bind'] in ('STB_GLOBAL', 'STB_WEAK'):
            exports.append([symbol.name, symbol['st_info']['type'], symbol['st_info']['bind'],
                            symbol['st_other']['visibility'], symbol['st_value'], symbol['st_size']])
    dynamic = elf.get_section_by_name('.dynamic')
    require(dynamic is not None, 'Dynamic section required')
    needed = [tag.needed for tag in dynamic.iter_tags('DT_NEEDED')]
    sonames = [tag.soname for tag in dynamic.iter_tags('DT_SONAME')]
    search_paths = ([tag.rpath for tag in dynamic.iter_tags('DT_RPATH')] +
                    [tag.runpath for tag in dynamic.iter_tags('DT_RUNPATH')])
    segments = []
    for segment in elf.iter_segments():
        require(segment['p_offset'] + segment['p_filesz'] <= len(data), 'Truncated segment')
        segments.append(dict(segment.header))
    require(any(p['p_type'] == 'PT_LOAD' for p in segments), 'No load segment')
    abi = {'flags': elf['e_flags'], 'osabi': elf['e_ident']['EI_OSABI'],
           'abi_version': elf['e_ident']['EI_ABIVERSION']}
    return {'sha256': digest(data), 'machine': elf['e_machine'], 'entry': elf['e_entry'], 'abi': abi,
            'sections': sections, 'program_headers': segments, 'needed': needed,
            'sonames': sonames, 'search_paths': search_paths, 'exports': sorted(exports), 'relocations': relocations,
            'build_paths': paths}


def compare(left, right):
    require(left['machine'] == right['machine'], 'Machine mismatch')
    a, b = left['sections'], right['sections']
    allocated = {n for n, s in a.items() if s['flags'] & 2} | {n for n, s in b.items() if s['flags'] & 2}
    changed = sorted(n for n in allocated if a.get(n) != b.get(n))
    bytes_changed = sorted(n for n in allocated if a.get(n, {}).get('sha256') != b.get(n, {}).get('sha256'))
    layout_changed = sorted(n for n in allocated if
                            {k: v for k, v in a.get(n, {}).items() if k != 'sha256'} !=
                            {k: v for k, v in b.get(n, {}).items() if k != 'sha256'})
    executable = sorted(n for n in allocated if (a.get(n, {}).get('flags', 0) | b.get(n, {}).get('flags', 0)) & 4)
    def export_abi(row):
        return [s[:4] + [s[5] if s[1] in ('STT_OBJECT', 'STT_TLS') else None] for s in row['exports']]
    return {'allocated_section_differences': changed,
            'allocated_byte_differences': bytes_changed,
            'section_layout_differences': layout_changed,
            'executable_section_differences': [n for n in executable if n in changed],
            'executable_byte_differences': [n for n in executable if n in bytes_changed],
            'exports_equal': left['exports'] == right['exports'],
            'export_abi_equal': export_abi(left) == export_abi(right),
            'elf_abi_equal': left['abi'] == right['abi'],
            'needed_equal': left['needed'] == right['needed'],
            'sonames_equal': left['sonames'] == right['sonames'],
            'search_paths_equal': left['search_paths'] == right['search_paths'],
            'relocations_equal': left['relocations'] == right['relocations'],
            'program_headers_equal': left['program_headers'] == right['program_headers'],
            'entry_equal': left['entry'] == right['entry'],
            'only_nonallocated_sections_removed': not changed and set(b) <= set(a),
            'removed_sections': sorted(set(a) - set(b))}


def summarize(row):
    return {key: value for key, value in row.items() if key not in ('exports', 'relocations')} | {
        'export_count': len(row['exports']), 'exports_sha256': canonical(row['exports']),
        'relocation_count': len(row['relocations']), 'relocations_sha256': canonical(row['relocations'])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--linked', type=Path, required=True)
    parser.add_argument('--packaged', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    for path in (args.linked, args.packaged):
        require(path.is_file() and not path.is_symlink(), 'Regular ELF input required')
    a, b = (inspect(p.read_bytes()) for p in (args.linked, args.packaged))
    require(a['machine'] == b['machine'] == 'EM_AARCH64', 'ARM64 candidate binaries required')
    result = {'linked': summarize(a), 'packaged': summarize(b), 'comparison': compare(a, b),
              'historical_binary_available': False, 'android_executed': False,
              'limits': 'Only these two supplied binaries were compared. Historical hashes do not supply historical section, export or relocation bytes.'}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    require(not result['comparison']['allocated_section_differences'] and
            all(result['comparison'][k] for k in ('exports_equal', 'export_abi_equal', 'elf_abi_equal',
                                                   'needed_equal', 'sonames_equal', 'search_paths_equal',
                                                   'relocations_equal', 'program_headers_equal', 'entry_equal')),
            'Linked/packaged loadable content differs')
    print(json.dumps({'loadable_sections_equal': True, 'exports': len(b['exports']),
                      'relocations': len(b['relocations']), 'build_paths': len(b['build_paths'])}))


if __name__ == '__main__':
    main()
