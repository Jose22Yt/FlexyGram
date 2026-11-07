"""Normalize only the separately tested, owner-requested launcher default presentation."""
import re


def before_glossy_default(data):
    def presentation(tag):
        return tag[0].replace(b'@mipmap/ic_flexy_glossy_round',b'@mipmap/ic_flexy_blue_round').replace(b'@mipmap/ic_flexy_glossy',b'@mipmap/ic_flexy_blue')
    data=re.sub(rb'<(?:application|intent-filter)\b[^>]*>',presentation,data,flags=re.S)
    data=data.replace(b'android:enabled="false"\n            android:name="org.telegram.messenger.FlexyNeonIcon"',b'android:enabled="true"\n            android:name="org.telegram.messenger.FlexyNeonIcon"')
    data=data.replace(b'android:enabled="true"\n            android:name="org.telegram.messenger.FlexyGlossyIcon"',b'android:enabled="false"\n            android:name="org.telegram.messenger.FlexyGlossyIcon"')
    return data
