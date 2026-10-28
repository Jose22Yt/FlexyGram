"""Scope checks are separate from Android input and physical acceptance."""
import hashlib, subprocess, unittest
import integration1282_contract as audit

class Integration1282(unittest.TestCase):
    def test_snapshot_keeps_native_draw_and_shared_blur_worker(self):
        def body(source, signature):
            start=source.index('{',source.index(signature));depth=1;end=start+1
            while depth:
                depth+=(source[end]=='{')-(source[end]=='}');end+=1
            return source[start:end]
        path='TMessagesProj/src/main/java/org/telegram/ui/Components/MotionBackgroundDrawable.java'
        current=(audit.ROOT/path).read_text();before=audit.original(path).decode()
        expected=body(before,'public void draw(Canvas canvas)').replace('updateAnimation();','if (advanceAnimation) updateAnimation();')
        self.assertEqual(expected,body(current,'private void drawSignatureContent'))
        snapshot=body(current,'public Bitmap getSignatureBlurBitmap()')
        self.assertIn('384f',snapshot);self.assertIn('drawSignatureContent(canvas, false)',snapshot)
        self.assertIn('signatureBlurStamp != stamp',snapshot)
        path='TMessagesProj/src/main/java/app/flexygram/bubbles/SignatureWallpaperBlur.java'
        current=(audit.ROOT/path).read_text();before=audit.original(path).decode()
        for method in ['private static Bitmap render(', 'private static boolean box(', 'private static Entry acquire(']:
            self.assertEqual(body(before,method),body(current,method),method)

    def test_reviewed_snapshot_rejects_unknown_bytes(self):
        audit.verify_current()
        for path in audit.spec()['reviewed']:
            data=(audit.ROOT/path).read_bytes()+b'\nUNREVIEWED'
            self.assertEqual(data,audit.restore(path,data),path)

    def test_historical_manifests_are_not_rewritten(self):
        for name in ['native_motion_restore_review.json','alpha1281_review.json','alpha1280_review.json']:
            path='tools/connected_alpha/'+name
            self.assertEqual(audit.original(path),(audit.ROOT/path).read_bytes(),path)

    def test_native_navigation_only_changes_by_reviewed_input_hook(self):
        path='TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java'
        data=(audit.ROOT/path).read_bytes()
        self.assertEqual(audit.original(path),audit.restore(path,data))
        source=data.decode()
        hook=source[source.index('private void nativeInstantTouchDown'):source.index('private boolean tabsEvents;')]
        self.assertLess(hook.index('!transitionAnimationInProgress'),hook.index('isVisibleDialogRow'))
        self.assertNotIn('MotionEvent.obtain',hook)
        self.assertNotIn('performClick',hook)
        self.assertNotIn('setDuration',hook)
        self.assertNotIn('setInterpolator',hook)
        self.assertEqual(1,hook.count('onAnimationEndCheck(true)'))

    def test_release_gates_only_increment_existing_version(self):
        for path in ['TMessagesProj/build.gradle','.github/workflows/connected-alpha-arm64.yml','tools/connected_alpha/build_private_apk.py']:
            data=(audit.ROOT/path).read_bytes()
            self.assertIn(b'1282',data)
            self.assertEqual(audit.original(path),data.replace(b'1282',b'1281'),path)

if __name__=='__main__': unittest.main()
