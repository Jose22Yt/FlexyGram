"""Test-APK asset, never an application module. Uses the reviewed cases verbatim."""
def runtime_android_api():
    # sys.getandroidapilevel is the Python BUILD minimum, not the running OS.
    from java import jclass
    return int(jclass('android.os.Build$VERSION').SDK_INT)

def run_probe(payload_json):
    import ctypes,hashlib,io,json,os,sys,types,unittest
    from pathlib import Path
    p=json.loads(payload_json);c=p['contract']
    def need(ok,message):
        if not ok:raise RuntimeError(message)
    def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    need(sys.version_info[:2]==(3,11),'Wrong Chaquopy Python minor')
    need(os.uname().machine=='aarch64' and hasattr(sys,'getandroidapilevel'),'Not Android ARM64 Python')
    need(sha(p['cases_path'])==c['runtime_cases_sha256'] and sha(p['font_path'])==c['font_sha256'],'Test fixture digest mismatch')
    module=types.ModuleType('flexygram_reviewed_runtime_cases');module.__file__=p['cases_path'];sys.modules[module.__name__]=module
    # The unchanged reviewed module installs its socket-denial audit hook here.
    exec(compile(Path(p['cases_path']).read_text(),p['cases_path'],'exec'),module.__dict__)
    from lxml import etree
    from PIL import ImageFont
    import PIL._imagingft
    def paths_for(name):
        result=set()
        for line in Path('/proc/self/maps').read_text().splitlines():
            fields=line.split(None,5)
            if len(fields)==6 and fields[5].startswith('/') and Path(fields[5]).name==name:result.add(fields[5])
        need(len(result)==1,'Missing/ambiguous loaded ELF: '+name)
        return Path(result.pop())
    libs=[];locations={}
    for name,h in c['libraries'].items():
        path=paths_for(name);need(path.is_file() and sha(path)==h,'Wrong loaded ELF: '+name)
        locations[name]=path;libs.append({'name':name,'sha256':h,'mapped_before':True,'path_basename':path.name})
    need(len({locations[x].parent for x in ['libxml2.so','libxslt.so','libexslt.so']})==1,'Unexpected XML dependency layout')
    module.LIBDIR=locations['libxml2.so'].parent;module.FTLIB=locations['libfreetype.so'];module.FONT=Path(p['font_path'])
    # Verify the application JNI policy without invoking MTProto/authentication entrypoints.
    jni=paths_for(c['jni_library'])
    need(sha(jni)==c['jni_sha256'],'Wrong mapped application JNI')
    native=ctypes.CDLL(str(jni));attest=native.flexygram_variant_policy;attest.argtypes=[];attest.restype=ctypes.c_char_p
    marker='FLEXYGRAM_POLICY:'+c['policy_scope']+':auth=0:transport=0:push=0:translation=0:plugins=0:restore=0'
    need(attest().decode()==marker,'Native policy scope/capabilities mismatch')
    class Result(unittest.TextTestResult):
        def __init__(self,*a,**k):super().__init__(*a,**k);self.rows=[]
        def addSuccess(self,t):super().addSuccess(t);self.rows.append({'id':t._testMethodName,'status':'PASS'})
        def addFailure(self,t,e):super().addFailure(t,e);self.rows.append({'id':t._testMethodName,'status':'FAIL'})
        def addError(self,t,e):super().addError(t,e);self.rows.append({'id':getattr(t,'_testMethodName',t.id()),'status':'ERROR'})
        def addSkip(self,t,r):super().addSkip(t,r);self.rows.append({'id':t._testMethodName,'status':'SKIP'})
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(module.NativeRuntimeCases)
    need(suite.countTestCases()==12,'Expected exactly twelve cases')
    output=io.StringIO();result=unittest.TextTestRunner(stream=output,resultclass=Result,verbosity=2).run(suite)
    for row in libs:
        name=row['name'];path=paths_for(name);need(path==locations[name] and sha(path)==row['sha256'],'Native mapping changed during test');row['mapped_after']=True
    plugins_not_loaded=not any(x in sys.modules for x in ['base_plugin','extera_utils.plugin_loader'])
    need(plugins_not_loaded,'Plugin loader unexpectedly active')
    return json.dumps({'android_api':runtime_android_api(),'python_build_android_api':sys.getandroidapilevel(),'python_minor':'3.11','python_version':sys.version.split()[0],'lxml_version':list(etree.LXML_VERSION),'libxml_version':list(etree.LIBXML_VERSION),'libxslt_version':list(etree.LIBXSLT_VERSION),'jni_sha256':c['jni_sha256'],'jni_scope_verified':True,'plugins_not_loaded':plugins_not_loaded,'libraries':libs,'cases':result.rows,'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'expected_failures':len(result.expectedFailures),'unexpected_successes':len(result.unexpectedSuccesses),'python_socket_audit_hook':True,'case_log':output.getvalue()})
