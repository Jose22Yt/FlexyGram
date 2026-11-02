#!/usr/bin/env python3
"""Compile exact radius methods in explicit dependency doubles; no Android/app benchmark."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
BASE = '340cd323f5f5809abc746507b2e252da71298720'
SOURCE = 'TMessagesProj/src/main/java/org/telegram/messenger/ImageReceiver.java'


def sources():
    before = subprocess.check_output(['git', 'show', BASE + ':' + SOURCE], cwd=ROOT, text=True)
    return before, (ROOT / SOURCE).read_text()


def radius_class(text, name):
    # Copy the complete public overload/delegation/config/recalculation path, not a formula rewrite.
    start = text.index('    public void setRoundRadius(int value)')
    end = text.index('    public void setRoundRadiusEnabled', start)
    shell = '''package perf;
public class _NAME_ {
 public final int[] roundRadius=new int[4]; public boolean isRoundRect;
 public float imageW; public int updates, digest;
 public Object currentImageDrawable, currentMediaDrawable, currentThumbDrawable, staticThumbDrawable;
 public Object imageShader, mediaShader;
 private void updateDrawableRadius(Object d){updates++;for(int r:roundRadius)digest=31*digest+r;digest=31*digest+System.identityHashCode(d);}
 public void avatar(boolean avatar,float width,boolean applied){oeIsAvatar=avatar;oeRadiusWidth=width;oeAvatarCornersApplied=applied;applyRoundRadiusInternal();}
 public void resize(float w){imageW=w;updateAvatarRadiusWidth();}
 public int[] requested(){return oeRequestedRoundRadius;}
_METHODS_
}'''
    return shell.replace('_NAME_', name).replace('_METHODS_', text[start:end])


CONFIG = '''package app.exteraless.appearance;
/** Preference dependency DOUBLE. Formula matches Kotlin default-corner branch; not real preference access. */
public class AppearanceConfig {
 public static final int AVATAR_CORNERS_MAX=28;
 public static int corners=14;public static boolean uniform;
 public static boolean avatarCornersDefault(){return corners>=28;}
 public static boolean singleCornerRadius(){return uniform;}
 public static int avatarCorners(){return corners;}
 public static int getAvatarCorners(float size){if(corners<=0)return 0;double value=size*corners/(28*2.0);if(value<=0)return 0;return (int)Math.ceil(value);}
}'''


def write_sources(directory):
    before, after = sources()
    files = {'perf/BaselineRadius.java': radius_class(before, 'BaselineRadius'),
             'perf/CandidateRadius.java': radius_class(after, 'CandidateRadius'),
             'app/exteraless/appearance/AppearanceConfig.java': CONFIG,
             'perf/RadiusProbe.java': (Path(__file__).parent / 'native/RadiusProbe.java.in').read_text()}
    for name, text in files.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return [directory / name for name in files]


def run(output):
    with tempfile.TemporaryDirectory(prefix='radius-differential-') as temp:
        temp = Path(temp)
        files = write_sources(temp)
        subprocess.run(['java', '-m', 'jdk.compiler/com.sun.tools.javac.Main', '-d', str(temp), *map(str, files)], check=True)
        # Disable host escape analysis explicitly: measures executed host allocations, NOT ART or wall-time.
        result = subprocess.check_output(['java', '-Xbatch', '-XX:-DoEscapeAnalysis', '-XX:TieredStopAtLevel=1',
                                          '-cp', str(temp), 'perf.RadiusProbe'], text=True)
        data = json.loads(result)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(data, indent=2) + '\n')
        print(json.dumps(data))
        return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT/'build/performance2/radius-host.json')
    run(parser.parse_args().out)
