package com.flexygram.performance;

import androidx.benchmark.macro.*;
import androidx.benchmark.macro.junit4.MacrobenchmarkRule;
import kotlin.Unit;
import org.junit.*;
import java.util.*;

/** Non-debuggable Alpha or Native Test target. Macrobenchmark emits traces and measured frame percentiles. */
public class DeviceBenchmarks {
    @Rule public final MacrobenchmarkRule benchmark=new MacrobenchmarkRule();
    private boolean scrollFixtureChecked;
    private int returnAnchorTop;
    private CompilationMode compilation(){
        String mode=androidx.test.platform.app.InstrumentationRegistry.getArguments().getString("flexy.compilation","baseline");
        if(mode.equals("none"))return new CompilationMode.None();
        Assert.assertEquals("Use none or baseline for comparable runs", "baseline",mode);
        return new CompilationMode.Partial(BaselineProfileMode.Require,0);
    }
    @Before public void requireFixture(){Journeys.fixture();}
    @Test public void coldStartup(){
        benchmark.measureRepeated(Journeys.PACKAGE,Arrays.asList(new StartupTimingMetric()),compilation(),StartupMode.COLD,20,
                scope->{scope.pressHome();return Unit.INSTANCE;},scope->{Journeys.launch(scope);return Unit.INSTANCE;});
    }
    @Test public void warmStartup(){
        benchmark.measureRepeated(Journeys.PACKAGE,Arrays.asList(new StartupTimingMetric()),compilation(),StartupMode.WARM,20,
                scope->{scope.pressHome();return Unit.INSTANCE;},scope->{Journeys.launch(scope);return Unit.INSTANCE;});
    }
    @Test public void openChatAndKeyboard(){
        benchmark.measureRepeated(Journeys.PACKAGE,Arrays.asList(new FrameTimingMetric()),compilation(),StartupMode.WARM,20,
                scope->{Journeys.launch(scope);return Unit.INSTANCE;},scope->{Journeys.openChat();Journeys.keyboard();Journeys.back();return Unit.INSTANCE;});
    }
    @Test public void keyboardInOpenChat() {
        benchmark.measureRepeated(Journeys.PACKAGE, Arrays.asList(new FrameTimingMetric()), compilation(),
                StartupMode.WARM, 20,
                scope -> {
                    Journeys.launch(scope);
                    Journeys.openChat();
                    return Unit.INSTANCE;
                },
                scope -> {
                    Journeys.keyboard();
                    return Unit.INSTANCE;
                });
    }

    @Test public void homeScroll() {
        benchmark.measureRepeated(Journeys.PACKAGE, Arrays.asList(new FrameTimingMetric()), compilation(), StartupMode.WARM, 20,
                scope -> {
                    Journeys.launch(scope);
                    if (!scrollFixtureChecked) {
                        Journeys.verifyDialogsCanScroll();
                        scrollFixtureChecked = true;
                    }
                    return Unit.INSTANCE;
                },
                scope -> { Journeys.scroll(); return Unit.INSTANCE; });
    }
    @Test public void openChatToVisibleHistory() {
        String message = Journeys.fixtureMessage();
        benchmark.measureRepeated(Journeys.PACKAGE, Arrays.asList(new FrameTimingMetric(),
                        new TraceSectionMetric("Flexy.benchmark.open_chat_to_visible_history",
                                TraceSectionMetric.Mode.First.INSTANCE, "openChatToVisibleHistory", false)),
                compilation(), StartupMode.WARM, 20,
                scope -> { Journeys.launch(scope); return Unit.INSTANCE; },
                scope -> { Journeys.openChatToVisibleHistory(message); return Unit.INSTANCE; });
    }
    @Test public void closeChatToSameListPosition() {
        benchmark.measureRepeated(Journeys.PACKAGE, Arrays.asList(new FrameTimingMetric(),
                        new TraceSectionMetric("Flexy.benchmark.return_to_chat_list",
                                TraceSectionMetric.Mode.First.INSTANCE, "closeChatToSameListPosition", false)),
                compilation(), StartupMode.WARM, 20,
                scope -> {
                    Journeys.launch(scope);
                    returnAnchorTop = Journeys.fixtureChatTop();
                    Journeys.openChat();
                    return Unit.INSTANCE;
                },
                scope -> {
                    Journeys.returnToChatList(returnAnchorTop);
                    return Unit.INSTANCE;
                });
    }

    @Test public void messageScroll(){
        String message = Journeys.fixtureMessage();
        benchmark.measureRepeated(Journeys.PACKAGE, Arrays.asList(new FrameTimingMetric()), compilation(), StartupMode.WARM, 20,
                scope -> {
                    Journeys.launch(scope);
                    Journeys.openChat();
                    if (!scrollFixtureChecked) {
                        Journeys.verifyMessagesCanScroll(message);
                        scrollFixtureChecked = true;
                    }
                    return Unit.INSTANCE;
                },
                scope -> { Journeys.scroll(); return Unit.INSTANCE; });
    }
    @Test public void settings(){
        benchmark.measureRepeated(Journeys.PACKAGE,Arrays.asList(new FrameTimingMetric()),compilation(),StartupMode.WARM,20,
                scope->{Journeys.launch(scope);return Unit.INSTANCE;},scope->{Journeys.settings();return Unit.INSTANCE;});
    }
}
