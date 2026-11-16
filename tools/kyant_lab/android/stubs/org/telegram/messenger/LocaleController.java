// Isolated test host API; production implementation is not replaced in the app.
package org.telegram.messenger;public class LocaleController{public static String getString(int id){return AndroidUtilities.context.getString(id); }public static boolean isRTL;}
