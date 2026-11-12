#!/usr/bin/env python3
"""Assert real AGP dry-run graphs isolate mandatory Alpha/Beta signing gates. No private inputs."""
from pathlib import Path
import re,sys
ALPHA=':TMessagesProj:validateConnectedAlphaConfiguration'
BETA=':TMessagesProj:validateFlexyGramBetaConfiguration'
def tasks(text):return set(re.findall(r'^(:TMessagesProj:[^\s]+) SKIPPED\s*$',text,re.M))
def verify(alpha,beta):
 a,b=tasks(alpha),tasks(beta)
 if ':TMessagesProj:assembleConnectedAlpha' not in a or ALPHA not in a:raise ValueError('Alpha graph lacks its mandatory validation/assembly')
 if BETA in a:raise ValueError('Alpha graph incorrectly requires the official Beta private key')
 if ':TMessagesProj:assembleBeta' not in b or BETA not in b:raise ValueError('Beta graph lacks its mandatory official identity validation/assembly')
 if ALPHA in b:raise ValueError('Beta graph incorrectly uses Alpha identity validation')
 return True
if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('Supply actual Alpha and Beta --dry-run logs')
 verify(Path(sys.argv[1]).read_text(),Path(sys.argv[2]).read_text())
 print('PASS actual Alpha/Beta AGP task graphs: separate mandatory signing validation; no private tasks executed')
