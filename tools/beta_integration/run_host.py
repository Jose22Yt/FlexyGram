"""Compile and execute real production geometry/effect/classifier math on the host JVM."""
from pathlib import Path
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
JAVA=ROOT/'TMessagesProj/src/main/java'
with tempfile.TemporaryDirectory(prefix='flexy-beta-host-') as work:
    files=[JAVA/'app/flexygram/bubbles/interaction/ContextPreviewPlacement.java',
           *sorted((JAVA/'app/flexygram/bubbles/deletion').glob('*Math.java')),
           JAVA/'app/flexygram/home/SignatureSmartPreviewPalette.java',
           JAVA/'app/flexygram/home/SignatureMiniPillClassifier.java',
           JAVA/'app/flexygram/home/SignatureSmartPillLayout.java',
           ROOT/'tools/delete_motion/DeleteMotionMathTest.java',ROOT/'tools/smart_pills/SmartPillHostTest.java',
           ROOT/'tools/beta_integration/PlacementProbe.java']
    subprocess.run(['javac','-d',work,*map(str,files)],check=True)
    for probe in ['PlacementProbe','DeleteMotionMathTest','SmartPillHostTest']:
        subprocess.run(['java','-cp',work,probe],check=True)
