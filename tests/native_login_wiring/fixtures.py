"""Unchanged bodies of original request classes + projected replies/framework doubles.
NOT a compile of complete TLRPC/LoginActivity; compile_originals.py records that separately.
"""
from pathlib import Path
import importlib.util,json,re,sys,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests/native_login'))
import tl_projection
COMPLETE=['TL_auth_sendCode','TL_auth_signIn','TL_auth_signUp','TL_auth_checkPassword','TL_auth_exportLoginToken','TL_auth_importLoginToken','TL_codeSettings','InputCheckPasswordSRP','TL_inputCheckPasswordSRP','TL_inputCheckPasswordEmpty','PasswordKdfAlgo','TL_passwordKdfAlgoUnknown','TL_passwordKdfAlgoSHA256SHA256PBKDF2HMACSHA512iter100000SHA256ModPow']
def original_class(source,name):
    masked=tl_projection.mask_comments(source)
    m=re.search(r'public static (?:abstract )?class '+re.escape(name)+r'\b[^\{]*\{',masked)
    if not m:raise RuntimeError('ORIGINAL_CLASS_MISSING:'+name)
    start=m.start();opening=m.end()-1;depth=0;quote=None;escaped=False
    for pos in range(opening,len(masked)):
        c=masked[pos]
        if quote:
            if escaped:escaped=False
            elif c=='\\':escaped=True
            elif c==quote:quote=None
        elif c in ['"',"'"]:quote=c
        elif c=='{':depth+=1
        elif c=='}':
            depth-=1
            if depth==0:return source[start:pos+1]
    raise RuntimeError('ORIGINAL_CLASS_UNBALANCED')
def write(folder):
    spec=importlib.util.spec_from_file_location('old_android_fixtures',ROOT/'tests/session_android/fixtures.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);old.write_fixtures(folder)
    metadata=tl_projection.write_projection(folder)
    base=ROOT/'TMessagesProj/src/main/java/org/telegram/tgnet';p=folder/'org/telegram/tgnet'
    original=(base/'TLRPC.java').read_text()
    parts=[d['header']+'{\n'+'\n'.join(d['fields'])+'\n}' for name,d in metadata['declarations'].items() if name not in COMPLETE and name not in ['Password','TL_password']]
    parts+=[original_class(original,name) for name in COMPLETE]
    (p/'TLRPC.java').write_text('package org.telegram.tgnet;import java.util.*;public class TLRPC {\n'+ '\n'.join(parts)+'\npublic static class EmailVerification extends TLObject {}\n}\n')
    account=(p/'tl/TL_account.java').read_text().replace('public boolean has_password;','public String hint;public boolean has_password;')
    account=account.replace('public static class TL_password extends Password','public static class TL_password extends Password')
    account=account.replace('public abstract class Password extends TLObject {','public abstract class Password extends TLObject {')
    # Correct typed return needed by the UNCHANGED getPassword method. It is a parser double.
    pattern=r'(public static (?:abstract )?class Password extends TLObject\s*\{)'
    account=re.sub(pattern,r'\1 public static Password TLdeserialize(InputSerializedData s,int c,boolean e){throw new UnsupportedOperationException("NO_WIRE_PARSER");}',account,count=1)
    (p/'tl/TL_account.java').write_text(account[:-2]+'\n'+original_class((base/'tl/TL_account.java').read_text(),'getPassword')+'\n}\n')
    (p/'TLMethod.java').write_bytes((base/'TLMethod.java').read_bytes())
    (p/'TLObject.java').write_text('''package org.telegram.tgnet;public class TLObject {
'''+''.join('public static final int FLAG_'+str(i)+'=1<<'+str(i)+';' for i in range(32))+'''
public static boolean hasFlag(int a,int b){return (a&b)!=0;}public static int setFlag(int a,int b,boolean v){return v?a|b:a&~b;}
public static TLObject TLdeserialize(InputSerializedData s,int c,boolean e){throw new UnsupportedOperationException("NO_WIRE_PARSER");}
public static <T extends TLObject>T TLdeserialize(Class<T> c,T value,InputSerializedData s,int n,boolean e){return value;}
public void serializeToStream(OutputSerializedData s){}public void readParams(InputSerializedData s,boolean e){}public TLObject deserializeResponse(InputSerializedData s,int n,boolean e){return null;}}
''')
    for name in ['InputSerializedData','OutputSerializedData','TLDataSourceType']:(p/(name+'.java')).write_bytes((base/(name+'.java')).read_bytes())
    (p/'NativeByteBuffer.java').write_text('package org.telegram.tgnet;public class NativeByteBuffer {}')
    (p/'Vector.java').write_text('''package org.telegram.tgnet;import java.util.*;public class Vector{
public static void serializeLong(OutputSerializedData s,ArrayList<Long> a){s.writeInt32(a.size());for(Long n:a)s.writeInt64(n);}
public static void serializeByteArray(OutputSerializedData s,ArrayList<byte[]> a){s.writeInt32(a.size());for(byte[] n:a)s.writeByteArray(n);}
public static ArrayList<byte[]> deserializeByteArray(InputSerializedData s,boolean e){throw new UnsupportedOperationException("NO_WIRE_PARSER");}}
''')
    messenger=folder/'org/telegram/messenger'
    (messenger/'SRPHelper.java').write_bytes((ROOT/'TMessagesProj/src/main/java/org/telegram/messenger/SRPHelper.java').read_bytes())
    (messenger/'Utilities.java').write_text('''package org.telegram.messenger;import java.math.BigInteger;public class Utilities {
public static java.security.SecureRandom random=new java.security.SecureRandom();
public static byte[] computeSHA256(byte[]... a){throw new IllegalStateException("SYNTHETIC_CONTEXT_SECRET_89123");}
public static byte[] computePBKDF2(byte[] a,byte[] b){throw new IllegalStateException("NO_HOST_CRYPTO");}
public static boolean isGoodPrime(byte[] p,int g){throw new IllegalStateException("NO_HOST_CRYPTO");}
public static boolean isGoodGaAndGb(BigInteger p,BigInteger q){throw new IllegalStateException("NO_HOST_CRYPTO");}}
''')
    return {'complete_original_request_classes':COMPLETE+['TL_account.getPassword'],'complete_original_files':['TLMethod.java','InputSerializedData.java','OutputSerializedData.java','SRPHelper.java'],'projected_reply_declarations':32,'full_TLRPC_compiled':False,'full_LoginActivity_compiled':False,'wire_parser_executed':False,'source_sha256':metadata['source_sha256'],'request_body_sha256':{name:hashlib.sha256(original_class(original,name).encode()).hexdigest() for name in COMPLETE}}
