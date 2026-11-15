"""Bound regex work by counted character accesses, independently of CPU timing."""
from test_render_work_reuse import JAVA, probe


def test_reserved_email_scan_is_linear_on_long_non_email_words(tmp_path):
    probe(tmp_path, {'Probe.java': '''import java.lang.reflect.*;import java.util.*;import java.util.regex.*;
import app.flexygram.inlineconverter.*;
public class Probe{
 static class Text implements CharSequence{
  final String text;long visits;Text(String s){text=s;}public int length(){return text.length();}
  public char charAt(int i){visits++;return text.charAt(i);}public CharSequence subSequence(int a,int b){return text.subSequence(a,b);}
 }
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args)throws Exception{
  Field f=InlineConversionScanner.class.getDeclaredField("RESERVED");f.setAccessible(true);Pattern pattern=(Pattern)f.get(null);
  for(int n:new int[]{64,512,4096}){
   Text text=new Text("a".repeat(n-1)+"1");Matcher matcher=pattern.matcher(text);check(!matcher.find());check(text.visits<20L*n);
  }
  String email="a".repeat(4090)+"@x.io";Matcher longEmail=pattern.matcher(email);check(longEmail.find()&&longEmail.start()==0&&longEmail.end()==email.length());
  List<String>expected=List.of("ana+20kg@example.com","José+tag@ejemplo.com","https://site.test/150USD","www.example.org/20kg","@usuario","#tema","`20 kg`");
  Matcher matcher=pattern.matcher(String.join(" ",expected));List<String>found=new ArrayList<>();while(matcher.find())found.add(matcher.group());check(found.equals(expected));
  String source="ana+20kg@example.com 20 kg";var matches=InlineConversionScanner.scan(source,Locale.US,null);
  check(matches.size()==1&&matches.get(0).raw.equals("20 kg")&&matches.get(0).start==source.lastIndexOf("20 kg"));
 }
}'''}, [JAVA/'app/flexygram/inlineconverter/InlineConversionScanner.java', JAVA/'app/flexygram/inlineconverter/InlineConversionMatch.java'])
