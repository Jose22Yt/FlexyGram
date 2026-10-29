"""Current-source gate independent of historical snapshots and physical acceptance."""
import hashlib, unittest
import integration1284_contract as audit

class Integration1284(unittest.TestCase):
    def test_exact_scope_and_unknown_mutations_are_rejected(self):
        audit.verify_current()
        for path in audit.spec()['reviewed']:
            raw=(audit.ROOT/path).read_bytes()+b'\nUNREVIEWED'
            self.assertEqual(raw,audit.restore(path,raw),path)

    def test_previous_review_manifests_remain_byte_identical(self):
        for name in ['stability1277','signature1278','alpha1280','alpha1281','native_motion_restore','integration1282','alpha1283']:
            path='tools/connected_alpha/'+name+'_review.json'
            self.assertEqual(audit.original(path),(audit.ROOT/path).read_bytes(),path)

    def test_message_rebound_belongs_only_to_the_selected_canvas_overlay(self):
        source=(audit.ROOT/'TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java').read_text()
        self.assertIn('selectedBubbleMotionMessage == cell.getMessageObject()',source)
        self.assertIn('canvas.scale(scale, scale,',source)
        self.assertGreaterEqual(source.count('selectedBubbleMotion.reset()'),3)
        motion=(audit.ROOT/'TMessagesProj/src/main/java/app/flexygram/bubbles/interaction/SelectedBubbleMotion.java').read_text()
        for forbidden in ['setScaleX','setScaleY','postDelayed','new Bitmap','ChatMessageCell']:
            self.assertNotIn(forbidden,motion)
        self.assertIn('running.removeAllUpdateListeners()',motion)
        self.assertIn('running.removeAllListeners()',motion)

    def test_native_protocol_and_authorized_identity_are_not_changed(self):
        for path in ['TMessagesProj/src/main/java/org/telegram/messenger/SendMessagesHelper.java',
                     'TMessagesProj/src/main/java/org/telegram/tgnet/ConnectionsManager.java',
                     'TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java',
                     'TMessagesProj/src/main/AndroidManifest.xml']:
            self.assertEqual(audit.original(path),(audit.ROOT/path).read_bytes(),path)
