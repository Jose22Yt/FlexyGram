"""Refresh only the explicit reviewed startup inventory; never hide arbitrary changes."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
PATHS=[
'TMessagesProj/src/main/java/app/flexygram/performance/StartupAccounts.java',
'TMessagesProj/src/main/java/org/telegram/messenger/ApplicationLoader.java',
'TMessagesProj/src/main/java/org/telegram/messenger/MessagesStorage.java',
'TMessagesProj/src/main/java/org/telegram/ui/LaunchActivity.java',
'TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java',
 'tools/connected_alpha/startup_contract.py','tools/connected_alpha/files_completion_contract.py',
 'tools/connected_alpha/test_startup.py','tools/connected_alpha/prepare_startup.py',
 'tools/connected_alpha/performance/STARTUP.md',
]
spec={'base':'175b299e0d4faeb246eca8e1be16a362a3a62213','reviewed':{path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest()for path in PATHS},'paths':sorted(PATHS+['tools/connected_alpha/startup_review.json'])}
(ROOT/'tools/connected_alpha/startup_review.json').write_text(json.dumps(spec,indent=2)+'\n')
