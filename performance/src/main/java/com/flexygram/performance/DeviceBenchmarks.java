package com.flexygram.performance;

import androidx.benchmark.macro.*;
import androidx.benchmark.macro.junit4.MacrobenchmarkRule;
import kotlin.Unit;
import org.junit.*;
import java.util.*;

/** Non-debuggable Alpha target. Macrobenchmark emits traces and measured frame percentiles. */
public class DeviceBenchmarks {
    @Rule public final MacrobenchmarkRule benchmark=new MacrobenchmarkRule();
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
    @Test public void openChatAndKeyboard(){
        benchmark.measureRepeated(Journeys.PACKAGE,Arrays.asList(new FrameTimingMetric()),compilation(),StartupMode.WARM,20,
                scope->{Journeys.launch(scope);return Unit.INSTANCE;},scope->{Journeys.openChat();Journeys.keyboard();Journeys.back();return Unit.INSTANCE;});
    }
    @Test public void messageScroll(){
        benchmark.measureRepeated(Journeys.PACKAGE,Arrays.asList(new FrameTimingMetric()),compilation(),StartupMode.WARM,20,
                scope->{Journeys.launch(scope);Journeys.openChat();return Unit.INSTANCE;},scope->{Journeys.scroll();return Unit.INSTANCE;});
    }
    @Test public void settings(){
        benchmark.measureRepeated(Journeys.PACKAGE,Arrays.asList(new FrameTimingMetric()),compilation(),StartupMode.WARM,20,
                scope->{Journeys.launch(scope);return Unit.INSTANCE;},scope->{Journeys.settings();return Unit.INSTANCE;});
    }
}
