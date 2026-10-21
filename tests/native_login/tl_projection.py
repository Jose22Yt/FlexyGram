"""Compile-time projections of EXACT selected declarations. No TL wire serialization or Android runtime."""
from pathlib import Path
import re,json,hashlib
ROOT=Path(__file__).resolve().parents[2]

def mask_comments(source):
    token=re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*[\s\S]*?\*/|//[^\n]*')
    return token.sub(lambda m:''.join('\n' if c=='\n' else ' ' for c in m.group()) if m.group().startswith(('/',)) else m.group(),source)

def block(source,name):
    source=mask_comments(source)
    match=re.search(r'public static (?:abstract )?class '+re.escape(name)+r'\s+extends\s+\w+\s*\{',source)
    if not match:raise RuntimeError('MISSING_REAL_TL_CLASS:'+name)
    opening=source.index('{',match.start());depth=0;quote=None;escaped=False
    for pos in range(opening,len(source)):
        char=source[pos]
        if quote:
            if escaped:escaped=False
            elif char=='\\':escaped=True
            elif char==quote:quote=None
        elif char in ['"',"'"]:quote=char
        elif char=='{':depth+=1
        elif char=='}':
            depth-=1
            if not depth:return source[match.start():opening],source[opening+1:pos]
    raise RuntimeError('UNBALANCED_TL_CLASS')

def write_projection(folder):
    base=ROOT/'TMessagesProj/src/main/java/org/telegram/tgnet'
    source=(base/'TLRPC.java').read_text();account=(base/'tl/TL_account.java').read_text()
    fields={
        'TL_error':['code','text'], 'auth_Authorization':[],
        'TL_auth_authorization':['setup_password_required','future_auth_token','user'],
        'TL_auth_authorizationSignUpRequired':['terms_of_service'], 'TL_help_termsOfService':[],
        'User':['id','phone'], 'TL_user':[],
        'auth_SentCode':['type','phone_code_hash','authorization'], 'TL_auth_sentCode':[],
        'TL_auth_sentCodeSuccess':[], 'TL_auth_sentCodePaymentRequired':[], 'auth_SentCodeType':['length'],
        'auth_LoginToken':[], 'TL_auth_loginToken':['expires','token'],
        'TL_auth_loginTokenMigrateTo':['dc_id','token'], 'TL_auth_loginTokenSuccess':['authorization'],
        'PasswordKdfAlgo':[], 'TL_passwordKdfAlgoUnknown':[],
        'TL_passwordKdfAlgoSHA256SHA256PBKDF2HMACSHA512iter100000SHA256ModPow':[]}
    for suffix in ('App','Sms','Call','FlashCall','MissedCall','SmsWord','SmsPhrase','FragmentSms','EmailCode','SetUpEmailRequired','FirebaseSms'):
        fields['TL_auth_sentCodeType'+suffix]=[]
    declarations={}
    def project(text,name,names):
        header,body=block(text,name);selected=[]
        for field in names:
            matches=re.findall(r'^        public ([\w.\[\]]+) '+re.escape(field)+r'\s*;',body,re.M)
            if len(matches)!=1:raise RuntimeError('MISSING_OR_AMBIGUOUS_REAL_FIELD:'+name+'.'+field)
            selected.append('public '+matches[0]+' '+field+';')
        declarations[name]={'header':header.strip(),'fields':selected}
        return header+'{\n'+'\n'.join(selected)+'\n}\n'
    body=''.join(project(source,name,names) for name,names in fields.items())
    package=folder/'org/telegram/tgnet';package.mkdir(parents=True,exist_ok=True)
    (package/'TLObject.java').write_text('package org.telegram.tgnet;public class TLObject {}\n')
    (package/'TLRPC.java').write_text('package org.telegram.tgnet;public class TLRPC {\n'+body+'}\n')
    body=project(account,'Password',['has_password','current_algo','srp_B','srp_id'])+project(account,'TL_password',[])
    (package/'tl').mkdir();(package/'tl/TL_account.java').write_text('package org.telegram.tgnet.tl;import org.telegram.tgnet.*;public class TL_account {\n'+body+'}\n')
    metadata={'source_sha256':{'TLRPC.java':hashlib.sha256((base/'TLRPC.java').read_bytes()).hexdigest(),'TL_account.java':hashlib.sha256((base/'tl/TL_account.java').read_bytes()).hexdigest()},'declarations':declarations,'wire_serializers_compiled':False}
    (folder/'projection.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return metadata
