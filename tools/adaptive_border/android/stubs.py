import importlib.util

def write(dest,root):
    spec=importlib.util.spec_from_file_location('bubble_host',root/'tools/connected_alpha/bubble_visual/stubs.py')
    host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
    stubs=dict(host.STUBS)
    stubs['org/telegram/ui/ActionBar/Theme.java']=stubs['org/telegram/ui/ActionBar/Theme.java'].replace(
        'public static final int key_chat_inBubble=1;',
        'public static final int key_chat_serviceBackground=120,key_chat_serviceBackgroundSelected=121; public static final int key_chat_inBubble=1;').replace(
        'public static int getColor(int k){',
        'public static int getColor(int k){if(k==120)return dark?0xff223344:0xffaabbcc;if(k==121)return dark?0xff334455:0xff99aabb;')
    for name,source in stubs.items():
        p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(source)
    java=root/'TMessagesProj/src/main/java'
    for name in ['org/telegram/ui/ActionBar/MessageDrawable.java','org/telegram/ui/Components/blur3/utils/NinePatchBuilder.java',
                 'app/flexygram/bubbles/BubbleConfig.java','app/flexygram/bubbles/BubbleStyle.java',
                 'app/flexygram/bubbles/BubbleOutline.java','app/flexygram/bubbles/BubbleFusion.java',
                 'app/flexygram/bubbles/SignatureBorderPath.java']:
        p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);source=(java/name).read_text()
        if name.endswith('SignatureBorderPath.java'):
            source=source.replace('public final class SignatureBorderPath {','public final class SignatureBorderPath { public static long testRebuilds;').replace('result.rewind();','testRebuilds++;result.rewind();')
        p.write_text(source)
