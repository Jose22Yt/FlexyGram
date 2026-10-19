// Compiled against original AAR, executed separately against AAR and facade.
import app.nekogram.translator.*;
import java.util.*;
public class BinaryContract extends BaseTranslator {
 protected Result translateImpl(String text,String from,String to){return Result.of(text,from);}
 public List<String> getTargetLanguages(){return Arrays.asList("en");}
 public static void main(String[] args)throws Exception {
  Result r=new BinaryContract().translate("synthetic","en","es");
  if(!r.translation.equals("synthetic")||!r.sourceLanguage.equals("en"))throw new AssertionError();
  if(r.hashCode()!=("synthetic".hashCode()^"en".hashCode()))throw new AssertionError();
  if(!r.equals(Result.of("synthetic","en")))throw new AssertionError();
  System.out.println("binary-contract-compatible");
 }
}
