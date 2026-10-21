"""Generate REVIEW-ONLY patches on temporary copies, never modifies the client.
Pinned #39 context. Token-aware brace scanning, explicit replacements, guard inventory.
"""
from pathlib import Path
import re,subprocess,tempfile,difflib,json,hashlib,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests/native_login_wiring'))
from fixtures import original_class
sys.path.insert(0,str(ROOT/'tests/native_login'))
from tl_projection import mask_comments
TARGET='TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java'
def span(source,signature):
    masked=mask_comments(source);start=masked.index(signature);op=masked.index('{',start);depth=0;quote=None;escape=False
    for pos in range(op,len(masked)):
        c=masked[pos]
        if quote:
            if escape:escape=False
            elif c=='\\':escape=True
            elif c==quote:quote=None
        elif c in ['"',"'"]:quote=c
        elif c=='{':depth+=1
        elif c=='}':
            depth-=1
            if depth==0:return start,op,pos+1
    raise RuntimeError('UNBALANCED_METHOD')
def prefix(source,signature,code,after_super=None):
    a,b,c=span(source,signature)
    if after_super:
        pos=source.index(after_super,b,c)+len(after_super)
    else:pos=b+1
    return source[:pos]+'\n'+code+'\n'+source[pos:]
def replace_once(source,old,new):
    if source.count(old)!=1:raise RuntimeError('AMBIGUOUS_ANCHOR:'+old[:80])
    return source.replace(old,new,1)
def main():
    out=ROOT/'patches/native-login-pages';out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        temp=Path(d)
        for path in [TARGET,'TMessagesProj/build.gradle']:
            p=temp/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/path).read_bytes())
        for patch in sorted((ROOT/'patches/native-login-wiring').glob('*.patch')):
            subprocess.run(['git','apply','--check',str(patch)],cwd=temp,check=True,capture_output=True)
            subprocess.run(['git','apply',str(patch)],cwd=temp,check=True,capture_output=True)
        old=(temp/TARGET).read_text();s=old
        helpers=(ROOT/'tools/native_login_pages/native_methods.txt').read_text()
        s=replace_once(s,'    private View cachedFragmentView;',helpers+'\n    private View cachedFragmentView;')
        # Existing #39 binding is not an activation path for these pages.
        s=prefix(s,'public void bindPreparedLocalLogin(', '        if (localLoginClosed()) throw new IllegalStateException("USE_CLOSED_LOCAL_PAGES_BINDING");')
        s=prefix(s,'public boolean onFragmentCreate()', '        if (localLoginClosed()) return preparedLocalSession != null && super.onFragmentCreate();')
        s=prefix(s,'public View createView(Context context)', '        if (localLoginClosed() && preparedLocalSession == null) throw new IllegalStateException("LOCAL_LOGIN_BINDING_REQUIRED");')
        s=s.replace('if (newAccount) {\n            ConnectionsManager.getInstance(currentAccount).setAppPaused','if (newAccount && !localLoginClosed()) {\n            ConnectionsManager.getInstance(currentAccount).setAppPaused')
        s=prefix(s,'public void onFragmentDestroy()', '        if (localLoginClosed()) detachClosedLocalView();')
        s=s.replace('        getNotificationCenter().removeObserver(this, NotificationCenter.didUpdateConnectionState);','        if (!localLoginClosed()) getNotificationCenter().removeObserver(this, NotificationCenter.didUpdateConnectionState);')
        s=s.replace('        getNotificationCenter().removeObserver(this, NotificationCenter.newSuggestionsAvailable);','        if (!localLoginClosed()) getNotificationCenter().removeObserver(this, NotificationCenter.newSuggestionsAvailable);')
        s=prefix(s,'public void saveSelfArgs(Bundle outState)', '        if (localLoginClosed()) { if (preparedLocalSession != null) { outState.putBoolean("flexygram_local_auth_restart", true); outState.putInt("flexygram_local_auth_account", currentAccount); } return; }')
        s=s.replace('activityMode == MODE_LOGIN && preparedLocalLoginBinding == null ? loadCurrentState','activityMode == MODE_LOGIN && !localLoginClosed() && preparedLocalLoginBinding == null ? loadCurrentState')
        s=prefix(s,'public boolean onBackPressed(boolean invoked)', '        if (localLoginClosed()) { if (!invoked) return currentViewNum == VIEW_PHONE_INPUT; if (currentViewNum == VIEW_PHONE_INPUT) { localCancelPages(); return true; } localCancelPages(); setPage(VIEW_PHONE_INPUT, true, null, true); return false; }')
        for signature in ['public void onRequestPermissionsResultFragment(', 'public void onActivityResultFragment(', 'private void clearCurrentState()', 'private void needShowProgress(', 'private void resendCodeFromSafetyNet(', 'private void onAuthSuccess(TLRPC.TL_auth_authorization res, boolean afterSignup)', 'private void fillNextCodeParams(Bundle params, TLRPC.auth_SentCode res, boolean animated)', 'public void didReceivedNotification(int id, int account, Object... args)']:
            # fillNextCodeParams signature differs between historical layers; require observed signature below.
            if signature in mask_comments(s):s=prefix(s,signature,'        if (localLoginClosed()) return;')
        for match in reversed(list(re.finditer(r'(?:private|public) (?:static )?void (?:fillNextCodeParams|needShowProgress)\([^{};]*\)\s*\{',mask_comments(s)))):
            s=s[:match.end()]+'\n        if (localLoginClosed()) return;\n'+s[match.end():]
        s=prefix(s,'public static Bundle loadCurrentState(', '        if (localLoginClosed()) return null;')
        for signature in ['public LoginActivity changeEmail(', 'public LoginActivity cancelAccountDeletion(', 'public LoginActivity changePhoneNumber()']:
            # all overloads are guarded below by their matched declaration
            pass
        for match in reversed(list(re.finditer(r'public LoginActivity (?:changeEmail|cancelAccountDeletion|changePhoneNumber)\([^{};]*\)\s*\{',mask_comments(s)))):
            s=s[:match.end()]+'\n        if (localLoginClosed()) throw new IllegalStateException("LOCAL_MODE_NOT_SUPPORTED");\n'+s[match.end():]
        s=prefix(s,'protected void onDialogDismiss(Dialog dialog)', '        if (localLoginClosed()) return;')
        for signature in ['public void onResume()', 'public void onPause()', 'public void onConfigurationChanged(']:
            s=prefix(s,signature,'        if (localLoginClosed() && !localViewActive()) return;')
        # Constrain page construction; retain the original view classes, not substitutes.
        s=re.sub(r'^(        views\[(VIEW_\w+)\] = new .+;)$',lambda m:('        if (!localLoginClosed() || io.github.jose22yt.flexygram.login.local.EphemeralPages.allowedPage('+m[2]+')) '+m[1].strip()),s,flags=re.M)
        s=s.replace('for (SlideView slideView : views) {','for (SlideView slideView : views) {\n                    if (slideView == null) continue;')
        s=replace_once(s,'            views[a].setVisibility(a == 0 ? View.VISIBLE : View.GONE);','            if (views[a] == null) continue;\n            views[a].setVisibility(a == 0 ? View.VISIBLE : View.GONE);')
        # createView has a cache return and a normal return. Attach only after original views exist.
        a,b,c=span(s,'public View createView(Context context)');chunk=s[a:c]
        chunk=chunk.replace('return fragmentView;','if (localLoginClosed()) attachClosedLocalView();\n            return fragmentView;')
        s=s[:a]+chunk+s[c:]
        s=prefix(s,'public void setPage(@ViewNumber int page, boolean animated, Bundle params, boolean back)', '        if (localLoginClosed() && (!localViewActive() || params != null || !io.github.jose22yt.flexygram.login.local.EphemeralPages.allowedPage(page))) return;\n        final io.github.jose22yt.flexygram.login.local.LocalTransitionFence localFence = preparedTransition;\n        final long localTransition = localLoginClosed() ? prepareLocalTransition() : 0;')
        a,b,c=span(s,'public void setPage(@ViewNumber int page, boolean animated, Bundle params, boolean back)');chunk=s[a:c]
        chunk=chunk.replace('            AnimatorSet pagesAnimation = new AnimatorSet();','            AnimatorSet pagesAnimation = new AnimatorSet();\n            if (localLoginClosed()) preparedPagesAnimation = pagesAnimation;')
        chunk=chunk.replace('public void onAnimationEnd(Animator animation) {','public void onAnimationEnd(Animator animation) {\n                    if (localLoginClosed() && (!localViewActive() || localFence != preparedTransition || !localFence.current(localTransition))) return;')
        s=s[:a]+chunk+s[c:]
        # Constructor controls which otherwise read backend/account state or initialize upload machinery.
        s=replace_once(s,'final boolean allowTestBackend = true;','final boolean allowTestBackend = !localLoginClosed();')
        init='''            imageUpdater = new ImageUpdater(false, ImageUpdater.FOR_TYPE_USER, false);
            imageUpdater.setOpenWithFrontfaceCamera(true);
            imageUpdater.setSearchAvailable(false);
            imageUpdater.setUploadAfterSelect(false);
            imageUpdater.parentFragment = LoginActivity.this;
            imageUpdater.setDelegate(this);'''
        s=replace_once(s,init,'            if (!localLoginClosed()) {\n'+init+'\n            }')
        # Block the overflow menu before proxy, API, backend or passkey actions.
        s=replace_once(s,'        moreButtonView.setDelegate(id -> {','        moreButtonView.setDelegate(id -> {\n            if (localLoginClosed()) return;')
        start=s.index('            String country = null;')
        end=s.index('            if (codeField.length() == 0) {\n                setCountryButtonText(null);',start)
        s=s[:start]+'            if (!localLoginClosed()) {\n'+s[start:end]+'            }\n'+s[end:]
        # Scoped class entry points. Methods guarded before any original body executes.
        classes=['PhoneView','LoginActivitySmsView','LoginActivityPasswordView','LoginActivityRegisterView','LoginActivityQrView']
        guard_inventory=[]
        for name in classes:
            sig='public class '+name;start,op,end=span(s,sig);body=s[start:end]
            routes={
              'PhoneView':'localPhoneNext(codeField.getText(), phoneField.getText());',
              'LoginActivitySmsView':'localCodeNext(codeFieldContainer.getCode());',
              'LoginActivityPasswordView':'localPasswordNext(codeField.getText());',
              'LoginActivityRegisterView':'localRegisterNext(firstNameField.getText(), lastNameField.getText());'}
            names_void=['saveStateParams','restoreStateParams','didReceivedNotification','onCancelPressed','onDestroyActivity','onHide','onShow','setParams','resendCode','createTimer','createCodeTimer','fillNumber','requestPasskey','loadCountries','showDebugMenu','didUploadPhoto','showTermsOfService','exportLoginToken']
            # Snapshot signatures first, then replace backwards by offsets to handle nested methods.
            masked=mask_comments(body)
            pattern=r'(?:public|private|protected)\s+(?:final\s+)?(void|boolean)\s+(\w+)\s*\([^{};]*?\)\s*\{'
            edits=[]
            for m in re.finditer(pattern,masked):
                typ,method=m[1],m[2];opening=m.end()-1
                if method=='onNextPressed' and name in routes:code='if (localLoginClosed()) { '+routes[name]+' return; }'
                elif method=='onBackPressed':code='if (localLoginClosed()) { localCancelPages(); return true; }'
                elif method in names_void:code='if (localLoginClosed()) { '+('localApplyPage('+('VIEW_PHONE_INPUT' if name=='PhoneView' else 'currentViewNum')+'); ' if method=='setParams' else '')+('clearClosedLocalInputs(); ' if method in ['onDestroyActivity','onHide'] else '')+('if (preparedLocalSession != null && localViewActive()) preparedLocalSession.loadPassword(preparedLocalView); ' if method=='onShow' and name=='LoginActivityPasswordView' else '')+'return; }'
                elif name=='PhoneView' and method in ['onAttachedToWindow','onDetachedFromWindow']:continue # handled after super below
                else:continue
                if method in ['onHide','onDestroyActivity']:
                    page={'PhoneView':'VIEW_PHONE_INPUT','LoginActivitySmsView':'(currentType == AUTH_TYPE_MESSAGE ? VIEW_CODE_MESSAGE : VIEW_CODE_SMS)','LoginActivityPasswordView':'VIEW_PASSWORD','LoginActivityRegisterView':'VIEW_REGISTER','LoginActivityQrView':'VIEW_QR_LOGIN'}[name]
                    code=code.replace('clearClosedLocalInputs();','localClearPage('+page+');' if name!='LoginActivityQrView' else '')
                edits.append((opening+1,'\n            '+code+'\n'));guard_inventory.append({'class':name,'method':method,'guard':'localLoginClosed'})
            for pos,insert in reversed(edits):body=body[:pos]+insert+body[pos:]
            if name=='PhoneView':
                body=body.replace('super.onAttachedToWindow();','super.onAttachedToWindow();\n            if (localLoginClosed()) return;').replace('super.onDetachedFromWindow();','super.onDetachedFromWindow();\n            if (localLoginClosed()) return;')
                body=body.replace('public void afterTextChanged(Editable editable) {','public void afterTextChanged(Editable editable) {\n                        if (localLoginClosed()) return;').replace('public void afterTextChanged(Editable s) {','public void afterTextChanged(Editable s) {\n                        if (localLoginClosed()) return;')
            # Block external/recovery/avatar/resend click handlers. Keep editor handlers which route onNextPressed.
            body=re.sub(r'(\.setOnClickListener\([^;\n]*?->\s*\{)',r'\1\n                if (localLoginClosed()) return;',body)
            # LinkSpan is a named click callback, not a lambda.
            body=body.replace('public void onClick(View widget) {','public void onClick(View widget) {\n                if (localLoginClosed()) return;')
            s=s[:start]+body+s[end:]
        # Disable Android automatic hierarchy saving at the root before returning the actual native view.
        a,b,c=span(s,'public View createView(Context context)');chunk=s[a:c].replace('if (localLoginClosed()) attachClosedLocalView();','if (localLoginClosed()) { fragmentView.setSaveEnabled(false); fragmentView.setSaveFromParentEnabled(false); if (android.os.Build.VERSION.SDK_INT >= 26) fragmentView.setImportantForAutofill(android.view.View.IMPORTANT_FOR_AUTOFILL_NO_EXCLUDE_DESCENDANTS); attachClosedLocalView(); }');s=s[:a]+chunk+s[c:]
        # Includes the OUTER notification callback and proxy helper, not just the first nested method.
        for match in reversed(list(re.finditer(r'(?:public|private|protected) void (?:didReceivedNotification|updateProxyButton)\([^{};]*\)\s*\{',mask_comments(s)))):
            if not s[match.end():].lstrip().startswith('if (localLoginClosed())'):
                s=s[:match.end()]+'\n        if (localLoginClosed()) return;\n'+s[match.end():]
        # No original view saves temporary credentials, even if invoked outside saveSelfArgs.
        patch=''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='a/'+TARGET,tofile='b/'+TARGET))
        (out/'0004-native-local-pages.patch').write_text(patch)
        gradle=(ROOT/'TMessagesProj/build.gradle').read_text()
        sources=['telegram-session-core/src/main/java','telegram-session-android/src/main/java','telegram-session-android/src/android/java','telegram-native-login/src/main/java','telegram-native-login/src/telegram/java','telegram-login-wiring/src/telegram/java','telegram-login-wiring/src/android/java','telegram-login-local-ui/src/main/java']
        insertion="    if (localLoginPagesEnabled) {\n        sourceSets.main.java.exclude('org/telegram/ui/LoginActivity.java')\n        sourceSets.realAlpha.java.srcDirs += [\n"+''.join("            rootProject.file('TMessagesProj_Modules/"+path+"'),\n" for path in sources)+"            rootProject.file('build/generated/flexygram-local-login/java')\n        ]\n    }\n"
        anchor="    sourceSets.main.jniLibs.srcDirs = ['./jni/']"
        newer=replace_once(gradle,anchor,anchor+'\n'+insertion)
        config="def localLoginPagesEnabled = providers.gradleProperty('flexygramLocalLoginPages').orNull == 'true'\nif (localLoginPagesEnabled && !realAlphaEnabled) throw new GradleException('FLEXYGRAM_LOCAL_PAGES_REQUIRES_REALALPHA')\nif (localLoginPagesEnabled && !rootProject.file('build/generated/flexygram-local-login/java/org/telegram/ui/LoginActivity.java').isFile()) throw new GradleException('FLEXYGRAM_LOCAL_PAGES_OVERLAY_REQUIRED')\n"
        marker="def realAlphaEnabled = providers.gradleProperty('flexygramRealAlpha').orNull == 'true'"
        config += "if (localLoginPagesEnabled) { def expected = new groovy.json.JsonSlurper().parse(rootProject.file('patches/native-login-pages/inventory.json')).overlay_sha256; def actual = java.security.MessageDigest.getInstance('SHA-256').digest(rootProject.file('build/generated/flexygram-local-login/java/org/telegram/ui/LoginActivity.java').bytes).encodeHex().toString(); if (actual != expected) throw new GradleException('FLEXYGRAM_LOCAL_PAGES_OVERLAY_MISMATCH') }\n"
        newer=replace_once(newer,marker,marker+'\n'+config)
        marker="        def flavor = builder.productFlavors.find { it.first == 'environment' }?.second"
        newer=replace_once(newer,marker,marker+"\n        if (localLoginPagesEnabled && !(flavor == 'realAlpha' && builder.buildType == 'debug')) { builder.enable = false; return }")
        (out/'0003-realalpha-local-pages-sources.patch').write_text(''.join(difflib.unified_diff(gradle.splitlines(True),newer.splitlines(True),fromfile='a/TMessagesProj/build.gradle',tofile='b/TMessagesProj/build.gradle')))
        (out/'inventory.json').write_text(json.dumps({'base':'40faca6b04563bcacd02d0947addd4c18ff81e81','target_sha256':hashlib.sha256((ROOT/TARGET).read_bytes()).hexdigest(),'overlay_sha256':hashlib.sha256(s.encode()).hexdigest(),'guarded_methods':guard_inventory,'qr_enabled':False,'review_only':True,'prerequisites':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'patches/native-login-wiring').glob('*.patch'))}},indent=2)+'\n')
        print('GENERATED_REVIEW_ONLY',len(guard_inventory))
if __name__=='__main__':main()
