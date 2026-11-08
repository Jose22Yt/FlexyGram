package app.exteraless.player;

import android.content.Context;
import org.telegram.messenger.BuildConfig;
import android.os.Bundle;

import org.telegram.messenger.MediaController;
import org.telegram.messenger.MessageObject;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.BottomSheet;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.AudioPlayerAlert;

import app.exteraless.appearance.AppearanceConfig;

public final class Md3Player {

    private Md3Player() {
    }

    public static boolean enabled() {
        return BuildConfig.CONNECTED_ALPHA || AppearanceConfig.md3Player();
    }

    public static boolean miniEnabled() {
        return false;
    }

    private static boolean handles(MessageObject messageObject) {
        return enabled() && messageObject != null && messageObject.isMusic();
    }

    public static BottomSheet create(Context context, Theme.ResourcesProvider resourcesProvider) {
        if (handles(MediaController.getInstance().getPlayingMessageObject())) {
            if (PlayerSheet.instance != null) {
                PlayerSheet.instance.dismissImmediately();
            }
            return new PlayerSheet(context, resourcesProvider);
        }
        return new AudioPlayerAlert(context, resourcesProvider);
    }

    public static void open(BaseFragment fragment, PlayerMiniView source) {
        if (fragment == null || fragment.getParentActivity() == null) {
            return;
        }
        MessageObject messageObject = MediaController.getInstance().getPlayingMessageObject();
        if (messageObject == null) {
            return;
        }
        BottomSheet sheet = create(fragment.getParentActivity(), fragment.getResourceProvider());
        fragment.showDialog(sheet);
    }

    public static boolean hidesContextPlayer(BaseFragment fragment, MessageObject messageObject) {
        return false;
    }
}
