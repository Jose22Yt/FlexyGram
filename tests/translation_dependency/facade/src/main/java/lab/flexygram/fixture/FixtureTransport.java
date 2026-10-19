// FlexyGram laboratory fixtures — GPL-3.0. No service implementation.
package lab.flexygram.fixture;
public interface FixtureTransport {
 enum Provider { MICROSOFT, DEEPL }
 interface Cancellation { boolean isCancelled(); }
 Response exchange(Provider provider,String text,String from,String to)throws Exception;
 final class Response {
  public final int status; public final String translation; public final String sourceLanguage;
  public Response(int status,String translation,String sourceLanguage){this.status=status;this.translation=translation;this.sourceLanguage=sourceLanguage;}
  @Override public String toString(){return "FixtureResponse{redacted}";}
 }
}
