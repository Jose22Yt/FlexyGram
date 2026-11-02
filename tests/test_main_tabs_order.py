"""Exercise production order persistence and lookup on a JVM, without Android or APK builds."""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def order_runner(tmp_path_factory):
    if not shutil.which("java"):
        pytest.skip("JDK required for navigation order tests")
    modules = subprocess.check_output(["java", "--list-modules"], text=True)
    if "jdk.compiler@" not in modules:
        pytest.skip("Java compiler module required for navigation order tests")
    tmp = tmp_path_factory.mktemp("tabs-order")
    sources = {
        "tw/nekomimi/nekogram/NekoConfig.java": '''package tw.nekomimi.nekogram;
public class NekoConfig {
 public static final Prefs prefs = new Prefs();
 public static Prefs getPreferences() { return prefs; }
 public static class Prefs {
  public String value;
  public String getString(String key, String fallback) { return value == null ? fallback : value; }
  public Prefs edit() { return this; }
  public Prefs putString(String key, String text) { value = text; return this; }
  public Prefs remove(String key) { value = null; return this; }
  public void apply() {}
 }
}''',
        "tw/nekomimi/nekogram/helpers/MainTabsHelper.java": '''package tw.nekomimi.nekogram.helpers;
public class MainTabsHelper {
 public static boolean contacts = true, profile = true;
 public static boolean hasContactsOrFeedTab() { return contacts; }
 public static boolean isProfileTabHidden() { return !profile; }
}''',
        "OrderTest.java": '''import java.util.*;
import app.exteraless.appearance.MainTabsOrder;
import tw.nekomimi.nekogram.NekoConfig;
import tw.nekomimi.nekogram.helpers.MainTabsHelper;
public class OrderTest {
 static void check(boolean ok) { if (!ok) throw new AssertionError(); }
 public static void main(String[] args) {
  if (args[0].equals("permutations")) {
   for (int a=0; a<4; a++) for (int b=0; b<4; b++)
    for (int c=0; c<4; c++) for (int d=0; d<4; d++) {
     List<Integer> expected = Arrays.asList(a,b,c,d);
     if (new HashSet<>(expected).size()!=4) continue;
     NekoConfig.prefs.value = a+","+b+","+c+","+d;
     check(MainTabsOrder.all().equals(expected));
     for (int id=0; id<4; id++) check(MainTabsOrder.position(id)==expected.indexOf(id));
     for (int i=0; i<4; i++) for (int j=0; j<4; j++) {
      List<Integer> swapped = new ArrayList<>(expected);
      Collections.swap(swapped, i, j);
      MainTabsOrder.swap(expected.get(i), expected.get(j));
      check(MainTabsOrder.all().equals(swapped));
      MainTabsOrder.swap(expected.get(i), expected.get(j));
      check(MainTabsOrder.all().equals(expected));
     }
   }
  } else {
   NekoConfig.prefs.value="2,garbage,2,9,0";
   check(MainTabsOrder.all().equals(Arrays.asList(2,0,1,3)));
   MainTabsHelper.contacts=false; MainTabsHelper.profile=false;
   check(MainTabsOrder.visible().equals(Arrays.asList(2,0)));
   check(MainTabsOrder.position(1)==-1 && MainTabsOrder.position(3)==-1);
   MainTabsOrder.swap(2,0);
   check(MainTabsOrder.visible().equals(Arrays.asList(0,2)));
   MainTabsHelper.contacts=true; MainTabsHelper.profile=true;
   check(MainTabsOrder.visible().equals(Arrays.asList(0,2,1,3)));
   MainTabsOrder.swap(-1,99);
   check(MainTabsOrder.all().equals(Arrays.asList(0,2,1,3)));
   MainTabsOrder.reset();
   check(MainTabsOrder.all().equals(Arrays.asList(0,1,2,3)));
  }
 }
}''',
    }
    for name, source in sources.items():
        target = tmp / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source)
    production = ROOT / "TMessagesProj/src/main/java/app/exteraless/appearance/MainTabsOrder.java"
    subprocess.run(["java", "-m", "jdk.compiler/com.sun.tools.javac.Main", "-d", str(tmp), str(production),
                    *[str(tmp / name) for name in sources]], check=True, capture_output=True)
    return lambda case: subprocess.run(["java", "-cp", str(tmp), "OrderTest", case],
                                       check=True, capture_output=True)


def test_all_orders_swap_and_resolve_screen_positions(order_runner):
    order_runner("permutations")


def test_hidden_tabs_corrupt_preferences_and_reset(order_runner):
    order_runner("hidden")
