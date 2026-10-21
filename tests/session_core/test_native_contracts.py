"""Host C++ against actual closed JNI policy and verbatim guard entries. Not JNI on Android."""
from pathlib import Path
import hashlib
import os
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'TMessagesProj_Modules/telegram-session-core/src/main/java'
HARNESS=Path(__file__).with_name('SessionHarness.java')

class NativeContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.folder=Path(cls.temp.name)
        source=cls.folder/'src';source.mkdir()
        policy=ROOT/'TMessagesProj/jni/real-alpha-policy.cmake'
        (source/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.16)\nproject(LocalNativeContract NONE)\ninclude("'+str(policy)+'")\n')
        scope=hashlib.sha256((ROOT/'gradle/real-alpha.json').read_bytes()).hexdigest()+':realAlpha'
        subprocess.run([os.environ['FLEXYGRAM_CMAKE'],'-S',str(source),'-B',str(cls.folder/'build'),'-DFLEXYGRAM_FLAVOR=realAlpha','-DFLEXYGRAM_POLICY_SCOPE='+scope],check=True,capture_output=True,text=True)
        cls.include=cls.folder/'build/flexygram-policy'
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_actual_cpp_attestation_consumed_by_actual_java_core(self):
        main=self.folder/'attest.cpp'
        main.write_text('#include <cstdio>\nextern "C" const char* flexygram_variant_policy();\nint main(){std::puts(flexygram_variant_policy());}')
        output=self.folder/'attest'
        subprocess.run(['c++','-std=c++17','-I'+str(self.include),str(main),str(ROOT/'TMessagesProj/jni/tgnet/VariantPolicy.cpp'),'-o',str(output)],check=True,capture_output=True,text=True)
        native=subprocess.run([str(output)],check=True,capture_output=True,text=True).stdout.strip()
        java=Path(os.environ['JAVA_HOME'])/'bin'
        subprocess.run([str(java/'javac'),'--release','8','-d',str(self.folder/'classes'),*map(str,SRC.rglob('*.java')),str(HARNESS)],check=True,capture_output=True,text=True)
        result=subprocess.run([str(java/'java'),'-cp',str(self.folder/'classes'),'io.github.jose22yt.flexygram.session.SessionHarness','actualNativeAttestation',native],check=True,capture_output=True,text=True)
        self.assertIn('LOCAL_ADAPTERS_ONLY',result.stdout)
        self.assertIn(':auth=0:transport=0:',native)
    def test_actual_native_guard_entries_do_not_reach_fake_transport_tail(self):
        def entry(path,signature):
            source=(ROOT/path).read_text();start=source.index(signature);opening=source.index('{',start)
            guard=source[opening+1:].strip().splitlines()[0]
            self.assertIn('flexygram::isolatedDiagnostic',guard)
            return guard
        manager='TMessagesProj/jni/tgnet/ConnectionsManager.cpp'
        socket='TMessagesProj/jni/tgnet/ConnectionSocket.cpp'
        send=entry(manager,'void ConnectionsManager::sendRequest(')
        init=entry(manager,'void ConnectionsManager::init(')
        open_socket=entry(socket,'void ConnectionSocket::openConnection(')
        open_internal=entry(socket,'void ConnectionSocket::openConnectionInternal(')
        cpp=self.folder/'guards.cpp';binary=self.folder/'guards'
        cpp.write_text('#include "'+str(ROOT/'TMessagesProj/jni/tgnet/DiagnosticPolicy.h')+'"\nint writes=0,initializations=0,sockets=0,freed=0;struct Object{~Object(){freed++;}};\nvoid send(Object*object){'+send+'\nwrites++;}\nvoid init(){'+init+'\ninitializations++;}\nvoid open(){'+open_socket+'\nsockets++;}\nvoid internal(){'+open_internal+'\nsockets++;}\nint main(){for(int i=0;i<50;i++){send(new Object);init();open();internal();}return writes||initializations||sockets||freed!=50;}')
        subprocess.run(['c++','-std=c++17','-I'+str(self.include),str(cpp),'-o',str(binary)],check=True,capture_output=True,text=True)
        self.assertEqual(subprocess.run([str(binary)]).returncode,0)
