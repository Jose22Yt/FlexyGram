"""Pinned realAlpha-only Java source selection. No edits to original client sources."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/native_login_pages'))
from materialize_overlay import materialize
BASE='57e3d958d161d77f3c468dcd9dc45644ccbc2fe7'

def prepare():
    receipt=materialize(ROOT/'build/generated/flexygram-local-login')
    source=ROOT/'TMessagesProj/src/realAlpha/java'
    output=ROOT/'build/generated/flexygram-local-login/realAlpha'
    inventory=json.loads((ROOT/'tools/real_alpha_local_login/originals.json').read_text())
    files={}
    for rel,expected in inventory.items():
        path=source/rel;data=path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('REALALPHA_ORIGINAL_CHANGED:'+rel)
        text=data.decode()
        if rel.endswith('/RealAlphaActivity.java'):
            text=text.replace('    private static final RealAlphaBootstrap BOOTSTRAP = new RealAlphaBootstrap();',
                '    private static final RealAlphaBootstrap BOOTSTRAP = new RealAlphaBootstrap();\n    private final org.telegram.ui.realalpha.local.RealAlphaLocalLoginHost localLab = new org.telegram.ui.realalpha.local.RealAlphaLocalLoginHost(this);')
            text=text.replace('        return fragment != null && fragment.getClass() == DialogsActivity.class;',
                '        return fragment != null && (fragment.getClass() == DialogsActivity.class || localLab.owns(fragment));')
            for expression,fragment in [('permitted(params.fragment) && super.needPresentFragment(layout, params)', 'params.fragment'), ('permitted(fragment) && super.needAddFragmentToStack(fragment, layout)', 'fragment')]:
                target='        return '+expression+';'
                if text.count(target)!=1:raise ValueError('REALALPHA_ADMISSION_CONTEXT_CHANGED')
                text=text.replace(target,'        boolean allowed=permitted('+fragment+');\n        localLab.recordNavigationAdmission('+fragment+',allowed);\n        return allowed && '+expression.split(' && ',1)[1]+';')
            marker='    @Override public void onNewIntent(Intent ignored) {'
            if text.count(marker)!=1:raise ValueError('REALALPHA_LIFECYCLE_CONTEXT_CHANGED')
            text=text.replace(marker,'''    @Override protected void onResume() {
        super.onResume();
        localLab.attachEntry();
    }

    @Override protected void onDestroy() {
        localLab.close();
        super.onDestroy();
    }

'''+marker)
            if text.count('localLab.owns(fragment)')!=1:raise ValueError('REALALPHA_ADMISSION_CONTEXT_CHANGED')
        result=text.encode()
        expected_output=json.loads((ROOT/'tools/real_alpha_local_login/generated.json').read_text())[rel]
        if hashlib.sha256(result).hexdigest()!=expected_output:raise ValueError('REALALPHA_GENERATOR_CHANGED:'+rel)
        target=output/rel
        if target.exists() and target.read_bytes()!=result:raise ValueError('REFUSING_DIFFERENT_GENERATED_REALALPHA')
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():target.write_bytes(result)
        files[rel]=hashlib.sha256(result).hexdigest()
    receipt.update({'integration_base':BASE,'realAlpha_overlay':files,'originals':inventory,'Android_compiled':False})
    (output.parent/'integration-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt
if __name__=='__main__':print(json.dumps(prepare()))
