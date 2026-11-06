package com.flexygram.performance;

import androidx.benchmark.macro.junit4.BaselineProfileRule;
import kotlin.Unit;
import org.junit.*;

/** Collects real ART rules on a provisioned device. Never fabricates profiles or runs from a normal build. */
public class ProfileGeneration {
    @Rule public final BaselineProfileRule profile=new BaselineProfileRule();
    @Before public void requireFixture(){Journeys.fixture();}
    @Test public void startup(){
        profile.collect(Journeys.PACKAGE,15,3,"flexy_startup",true,true,
                scope->{scope.pressHome();Journeys.launch(scope);return Unit.INSTANCE;});
    }
    @Test public void chat(){
        profile.collect(Journeys.PACKAGE,scope->{Journeys.launch(scope);Journeys.openChat();Journeys.scroll();Journeys.keyboard();Journeys.back();return Unit.INSTANCE;});
    }
    @Test public void settings(){
        profile.collect(Journeys.PACKAGE,scope->{Journeys.launch(scope);Journeys.settings();return Unit.INSTANCE;});
    }
}
