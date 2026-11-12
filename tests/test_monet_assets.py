"""Reviewed icon provenance and getter-only fragment palette integration."""
import json,re,zipfile
from pathlib import Path
from test_render_work_reuse import probe,JAVA
ROOT=Path(__file__).resolve().parents[1]

def test_reviewed_resources_are_losslessly_imported_and_all_have_coverage():
    assets=json.loads((ROOT/'tools/settings_monet/approved_assets.json').read_text())
    assert len(assets)==85
    assert len({a['drawable'] for a in assets})==85
    res=ROOT/'TMessagesProj/src/main/res'
    with zipfile.ZipFile(ROOT/'docs/design-reviews/FlexyGram_Duotono_Monet_Bordes_Pulidos.zip') as z:
        for a in assets:
            path=res/'drawable-nodpi'/(a['drawable']+'.png')
            assert path.read_bytes()==z.read('FlexyGram_Duotono_Monet_Bordes_Pulidos/android/res/drawable-nodpi/'+path.name)
            assert (res/'raw'/(a['coverage']+'.png')).is_file()
            assert min(a['size'])>0


def test_specialized_settings_palette_initialization_uses_fragment_getter_setter_contract(tmp_path):
    paths=[JAVA/'tw/nekomimi/nekogram/settings/BaseNekoXSettingsActivity.java',JAVA/'app/exteraless/settings/OpenExteraAppNavigationActivity.java']
    paths += [JAVA/f'app/exteraless/plugins/ui/{n}.java' for n in ['PluginsActivity','PluginsInfoActivity','PluginPermissionsActivity','PluginSettingsActivity','PluginActivityLogActivity']]
    methods=[]
    for i,path in enumerate(paths):
        text=path.read_text()
        statements=re.findall(r'setResourceProvider\(app\.flexygram\.settings\.signature\.SettingsTheme\.wrap\(getResourceProvider\(\)\)\);',text)
        assert statements,path
        methods.append('void initialize'+str(i)+'(){'+statements[0]+'}')
    probe(tmp_path,{
        'app/flexygram/settings/signature/SettingsTheme.java':'package app.flexygram.settings.signature;public class SettingsTheme{public static Object wrap(Object o){return o;}}',
        'Probe.java':'''class FragmentContract{Object provider=new Object();public Object getResourceProvider(){return provider;}public void setResourceProvider(Object value){provider=value;}}
public class Probe extends FragmentContract{METHODS public static void main(String[]args){Probe p=new Probe();CALLS}}'''.replace('METHODS',''.join(methods)).replace('CALLS',''.join('p.initialize'+str(i)+'();' for i in range(len(paths))))
    })
