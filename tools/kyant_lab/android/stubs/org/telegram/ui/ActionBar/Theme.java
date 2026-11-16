// Isolated test host API; production implementation is not replaced in the app.
package org.telegram.ui.ActionBar;public class Theme{public static final int key_windowBackgroundWhite=1,key_windowBackgroundGray=2,key_windowBackgroundWhiteBlackText=3;public static int getColor(int key){return key==2?0xff121212:key==3?0xff111111:0xffeeeeee;}public static boolean isCurrentThemeDark(){return false;}}
