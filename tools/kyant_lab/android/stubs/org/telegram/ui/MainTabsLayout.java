// Isolated test host API; production implementation is not replaced in the app.
package org.telegram.ui;public class MainTabsLayout extends android.widget.LinearLayout{public MainTabsLayout(android.content.Context c){super(c);}public boolean isViewVisible(android.view.View v){return true;}}
