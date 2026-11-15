"""Normalize only the separately tested, owner-requested launcher default presentation."""
import re


def before_glossy_default(data):
    def presentation(tag):
        return tag[0].replace(b'@mipmap/ic_flexy_glossy_round',b'@mipmap/ic_flexy_blue_round').replace(b'@mipmap/ic_flexy_glossy',b'@mipmap/ic_flexy_blue')
    data=re.sub(rb'<(?:application|intent-filter)\b[^>]*>',presentation,data,flags=re.S)
    data=data.replace(b'android:enabled="false"\n            android:name="org.telegram.messenger.FlexyNeonIcon"',b'android:enabled="true"\n            android:name="org.telegram.messenger.FlexyNeonIcon"')
    data=data.replace(b'android:enabled="true"\n            android:name="org.telegram.messenger.FlexyGlossyIcon"',b'android:enabled="false"\n            android:name="org.telegram.messenger.FlexyGlossyIcon"')
    return data


def without_native_trial_components(data):
    data=data.replace(b'vnd.com.flexygram.messenger.nativebaseline.android.',b'vnd.io.github.jose22yt.flexygram.alpha.android.')
    data=data.replace(b'android:label="FlexyGram Native Test"', b'android:label="@string/NagramX"')
    data=re.sub(rb'            <!-- FlexyStudio:.*?            <!-- exteraless plugins:',b'            <!-- exteraless plugins:',data,flags=re.S)
    data=re.sub(rb'\n        <provider android:name="app\.flexygram\.studio\.FlexyStudioProvider".*?</provider>\n',b'\n',data,flags=re.S)
    data=re.sub(rb'        <service android:name="app\.flexygram\.studio\.FlexyStudioCleanup"[^>]+/>\n',b'',data)
    return data
