// FlexyGram laboratory facade — @Lukhou23. GPL-3.0; see repository LICENSE.
// Independent implementation against the recorded consumed ABI. Not wired into Android.
package app.nekogram.translator;
/** Fixed diagnostics only: never keeps transport messages, causes or response bodies. */
public final class FacadeFailure extends IllegalStateException {
 public final int status;
 FacadeFailure(String code,int status){super(code);this.status=status;}
}
