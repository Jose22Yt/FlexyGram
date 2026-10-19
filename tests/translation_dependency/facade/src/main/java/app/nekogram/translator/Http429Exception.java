// FlexyGram laboratory facade — @Lukhou23. GPL-3.0; see repository LICENSE.
// Independent implementation against the recorded consumed ABI. Not wired into Android.
package app.nekogram.translator;
public class Http429Exception extends java.io.IOException {
 public Http429Exception(){super("TRANSLATION_RATE_LIMITED");}
}
