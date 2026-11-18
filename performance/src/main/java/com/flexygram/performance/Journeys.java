package com.flexygram.performance;

import android.os.Bundle;
import androidx.benchmark.macro.MacrobenchmarkScope;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.uiautomator.*;
import org.junit.Assert;
import org.junit.Assume;

/** Synthetic, pre-provisioned test account only. Never logs a title, sends messages or resets data. */
final class Journeys {
    static final String PACKAGE=InstrumentationRegistry.getArguments().getString("flexy.targetPackage", "io.github.jose22yt.flexygram.alpha");
    private static final long TIMEOUT=15_000;
    static final UiDevice device=UiDevice.getInstance(InstrumentationRegistry.getInstrumentation());
    private Journeys() { }
    static String fixture(){
        String name=InstrumentationRegistry.getArguments().getString("flexy.fixtureChat");
        Assume.assumeTrue("Provision a synthetic chat and supply flexy.fixtureChat; no measurements were collected.",name!=null&&!name.isBlank());
        return name;
    }
    private static boolean composerVisible(){return device.hasObject(By.pkg(PACKAGE).clazz(java.util.regex.Pattern.compile(".*EditText.*")));}
    private static boolean homeVisible(){return device.hasObject(By.pkg(PACKAGE).text(fixture()))&&!composerVisible();}
    static void launch(MacrobenchmarkScope scope){
        scope.startActivityAndWait();device.waitForIdle();
        // Warm iterations may resume the previous fixture chat or settings page.
        for(int i=0;i<4&&!homeVisible();i++){device.pressBack();device.waitForIdle();}
        home();
    }
    static void home(){Assert.assertTrue("The synthetic chat list is not ready; refusing to measure a login or splash screen.",device.wait(Until.hasObject(By.pkg(PACKAGE).text(fixture())),TIMEOUT)&&!composerVisible());}
    private static UiObject2 fixtureChatRow() {
        UiObject2 chat = device.wait(Until.findObject(By.pkg(PACKAGE).text(fixture())), TIMEOUT);
        Assert.assertNotNull("Synthetic fixture missing", chat);
        return chat;
    }
    static void openChat(){
        fixtureChatRow().click();
        Assert.assertTrue("Composer not visible",device.wait(Until.hasObject(By.pkg(PACKAGE).clazz(java.util.regex.Pattern.compile(".*EditText.*"))),TIMEOUT));
    }
    static void openChatToVisibleHistory(String message) {
        // ChatMessageCell appends accessible metadata to the message text.
        BySelector visibleMessage = By.pkg(PACKAGE).textContains(message);
        Assert.assertFalse("Choose a fixture message absent from the home screen",
                device.hasObject(visibleMessage));
        UiObject2 chat = fixtureChatRow();
        android.os.Trace.beginSection("Flexy.benchmark.open_chat_to_visible_history");
        try {
            chat.click();
            Assert.assertTrue("Synthetic history did not become visible",
                    device.wait(Until.hasObject(visibleMessage), TIMEOUT));
        } finally {
            android.os.Trace.endSection();
        }
    }
    static void scroll(){
        int x=device.getDisplayWidth()/2,high=device.getDisplayHeight()*3/10,low=device.getDisplayHeight()*7/10;
        for(int i=0;i<3;i++){Assert.assertTrue(device.swipe(x,low,x,high,24));Assert.assertTrue(device.swipe(x,high,x,low,24));}
    }
    static void keyboard(){
        UiObject2 edit=device.wait(Until.findObject(By.pkg(PACKAGE).clazz(java.util.regex.Pattern.compile(".*EditText.*"))),TIMEOUT);
        Assert.assertNotNull(edit);edit.click();device.waitForIdle();device.pressBack();device.waitForIdle();
    }
    static void back(){if(!homeVisible()){device.pressBack();device.waitForIdle();}home();}
    static void settings(){
        Bundle args=InstrumentationRegistry.getArguments();String menu=args.getString("flexy.menuDescription"),settings=args.getString("flexy.settingsLabel");
        Assume.assumeTrue("Supply the synthetic fixture's localized Settings label",settings!=null);
        if (PACKAGE.equals("com.flexygram.messenger.nativebaseline")) {
            UiObject2 tab=device.findObject(By.pkg(PACKAGE).text(settings));
            if (tab==null)tab=device.findObject(By.pkg(PACKAGE).desc(settings));
            if (tab!=null){tab.click();device.waitForIdle();scroll();return;}
        }
        Assume.assumeTrue("Supply the localized navigation menu description for drawer navigation",menu!=null);
        UiObject2 button=device.wait(Until.findObject(By.pkg(PACKAGE).desc(menu)),TIMEOUT);Assert.assertNotNull(button);button.click();
        UiObject2 row=device.wait(Until.findObject(By.pkg(PACKAGE).text(settings)),TIMEOUT);Assert.assertNotNull(row);row.click();device.waitForIdle();
    }
}
