from pathlib import Path
import json,subprocess,hashlib,shutil,time
r=Path.cwd();spec=json.loads((r/'investigation/link-argv-private.json').read_text());args=spec['args'];original=Path(args[spec['output_index']]);out=r/'investigation/relinked/libtmessages.49.so';out.parent.mkdir(exist_ok=True);args[spec['output_index']]=str(out)
start=time.monotonic();p=subprocess.run(args,cwd=spec['cwd'],capture_output=True,text=True);(r/'investigation/relink.log').write_text(p.stdout+p.stderr)
if p.returncode:raise ValueError('Link-only experiment failed; see log')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result={'operation':'link_only_existing_objects_no_compilation','exit_code':p.returncode,'seconds':round(time.monotonic()-start,2),'linked_original_sha256':sha(original),'linked_repeated_sha256':sha(out),'linked_identical':sha(original)==sha(out),'apk_rebuilt':False,'original_outputs_modified':False}
stripped=out.with_name('libtmessages-stripped.so');shutil.copyfile(out,stripped);strip=r/'toolchains/sdk/ndk/27.2.12479018/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip'
subprocess.run([str(strip),'--strip-unneeded',str(stripped)],check=True,capture_output=True)
result['stripped_repeated_sha256']=sha(stripped);result['packaged_sha256']=sha(r/'investigation/libtmessages-packaged.so');result['strip_matches_packaged']=result['stripped_repeated_sha256']==result['packaged_sha256']
assert result['linked_identical'] and result['strip_matches_packaged'],result
(r/'investigation/relink-determinism.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
