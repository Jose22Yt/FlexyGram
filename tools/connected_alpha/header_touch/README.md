# Header touch regression

Run with JDK 17+, Maven, Android API 37 and build-tools 36:

```sh
python tools/connected_alpha/header_touch/run.py --sdk-root "$ANDROID_HOME"
```

The fixture extracts the production `ChatAvatarContainer.onMeasure` entry
verbatim. Android views receive down/up events separated by a forced measure.
The overflow listener opens a real Android `PopupWindow`; the call listener
counts dispatches. A third test checks the inactive header hides its controls.
Account services, complete navigation and header geometry are explicit fixtures.
This is an Android framework regression test, not a full client/device test.

Before the fix, the menu and call tests failed: temporarily setting the controls
to `GONE` during measurement cancelled their pending clicks. With the active
header branch evaluated first, all three tests pass. The UI beta workflow runs
this probe before assembling the APK.

The host-width regression also extracts the chat root's production margin block.
Signature geometry uses the full ActionBar width. An old native-menu right margin
of 52/92 dp reduced the avatar container's touch area while its overflow remained
drawn outside it. With title centering off, the unpatched code loses the overflow
click. The fixed code opens a real PopupWindow and dispatches the call click at
320, 400 and 800 px widths, with and without native action flags. A separate test
checks that native headers retain their original reserved menu space. Header
geometry and account services remain fixtures; no logged-in device is exercised.
