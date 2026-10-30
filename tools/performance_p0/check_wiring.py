#!/usr/bin/env python3
"""Check lifecycle/queue integration and byte-identical protocol, signing and native sources."""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
BASE='0030904ae2e41d7720f43b7906c6a302ed339839'
JAVA=ROOT/'TMessagesProj/src/main/java'


def block(source,token):
    start=source.index(token);a=source.index('{',start);depth=0
    for i in range(a,len(source)):
        if source[i]=='{':depth+=1
        elif source[i]=='}':
            depth-=1
            if depth==0:return source[start:i+1]
    raise ValueError('Unclosed source block')


def main():
    def text(name):return (JAVA/name).read_text()
    def old(name):return subprocess.check_output(['git','show',BASE+':TMessagesProj/src/main/java/'+name],cwd=ROOT,text=True)
    connection='org/telegram/tgnet/ConnectionsManager.java'
    for method in ['public void checkConnection()', 'protected byte getIpStrategy()', 'public int getConnectionState()']:
        assert block(text(connection),method)==block(old(connection),method),method
    native=(ROOT/'TMessagesProj/jni/tgnet/ConnectionsManager.cpp').read_text()
    for method in ['void ConnectionsManager::setIpStrategy', 'void ConnectionsManager::setNetworkAvailable']:
        assert 'scheduleTask(' in block(native,method)
    assert 'task -> Utilities.stageQueue.postRunnable(task), this::checkConnection' in text(connection)
    loader=text('org/telegram/messenger/ApplicationLoader.java')
    receive=block(loader,'public void onReceive(Context context, Intent intent)')
    assert '.scheduleConnectionCheck()' in receive and '.checkConnection()' not in receive
    ensure=block(loader,'private static void ensureCurrentNetworkGet()')
    assert 'lastNetworkCheck =' not in ensure and 'SystemClock.elapsedRealtime()' in ensure
    actual_query=block(loader,'private static void ensureCurrentNetworkGet(boolean force)')
    assert 'lastNetworkCheck = SystemClock.elapsedRealtime()' in actual_query
    assert actual_query.count('invalidateNetworkSnapshot();')==3 and 'public void onLost' in actual_query
    for method in ['private static void prepareSelectedDialogs()']:
        assert block(loader,method)==block(old('org/telegram/messenger/ApplicationLoader.java'),method)
    activity=text('org/telegram/ui/LaunchActivity.java')
    assert 'refreshRateMonitor.start();' in block(activity,'protected void onResume()')
    for method in ['protected void onPause()','protected void onDestroy()']:
        assert 'refreshRateMonitor.stop();' in block(activity,method)
    recycler=text('org/telegram/ui/Components/RecyclerListView.java')
    assert 'scrollFrameRateHint.setScrolling(newState != SCROLL_STATE_IDLE)' in recycler
    assert 'scrollFrameRateHint.setScrolling(false)' in block(recycler,'protected void onDetachedFromWindow()')
    frozen=['config/signing','gradle.properties',
            'TMessagesProj/src/main/AndroidManifest.xml','TMessagesProj/src/connectedAlpha','TMessagesProj/src/beta',
            'TMessagesProj/jni','TMessagesProj/chaquopy','TMessagesProj/src/main/java/org/telegram/messenger/MessagesController.java',
            'TMessagesProj/src/main/java/org/telegram/messenger/MessagesStorage.java',
            'TMessagesProj/src/main/java/org/telegram/messenger/SendMessagesHelper.java',
            'TMessagesProj/src/main/java/org/telegram/messenger/NotificationsController.java',

            'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java']
    assert not subprocess.check_output(['git','diff',BASE,'--',*frozen],cwd=ROOT)
    import sys
    sys.path.insert(0,str(ROOT/'tools/connected_alpha'))
    from native_context135_contract import restore as current_overlay
    reviewed_build = current_overlay('TMessagesProj/build.gradle', (ROOT/'TMessagesProj/build.gradle').read_bytes()).decode()
    assert reviewed_build.replace('def verCode = 1287','def verCode = 1286') == subprocess.check_output(['git','show',BASE+':TMessagesProj/build.gradle'],cwd=ROOT,text=True)
    from work1_contract import restore,original
    signing='gradle/flexygram-beta.gradle'
    assert restore(signing,(ROOT/signing).read_bytes())==original(signing)
    for name in ['org/telegram/ui/ChatActivity.java','org/telegram/ui/Cells/ChatMessageCell.java']:
        path='TMessagesProj/src/main/java/'+name
        assert restore(path,(ROOT/path).read_bytes())==original(path)
    print('PASS: native protocol bodies, local dialogs gate, identity/JNI and gesture ownership unchanged; lifecycle/queue wiring checked.')


if __name__=='__main__':main()
