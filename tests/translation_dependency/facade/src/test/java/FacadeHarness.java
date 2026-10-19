// Synthetic offline parity fixtures. GPL-3.0.
import app.nekogram.translator.*;
import lab.flexygram.fixture.FixtureTransport;
import java.util.*;
import java.util.concurrent.CancellationException;
import java.io.IOException;
public class FacadeHarness {
 static final String PRIVATE="SYNTHETIC_PRIVATE_💎_&amp;_<b>text</b>";
 static void ok(boolean condition){if(!condition)throw new AssertionError("fixture mismatch");}
 static class Transport implements FixtureTransport {
  int calls; int status=200; String mode="ok"; Provider seen;String text,from,to;boolean cancelled;
  public Response exchange(Provider p,String text,String from,String to)throws Exception {
   calls++;seen=p;this.text=text;this.from=from;this.to=to;
   if(mode.equals("tainted")) {
    try {new MicrosoftTranslator().translate("synthetic",null,"en");}
    catch(FacadeFailure e){e.initCause(new IOException(PRIVATE));throw e;}
   }
   if(mode.equals("io"))throw new IOException(PRIVATE);
   if(mode.equals("cancel"))throw new CancellationException(PRIVATE);
   if(mode.equals("interrupt"))throw new InterruptedException(PRIVATE);
   if(mode.equals("runtime"))throw new IllegalArgumentException(PRIVATE);
   if(mode.equals("null"))return null;
   if(mode.equals("inflight"))cancelled=true;
   return new Response(status,mode.equals("invalid")?null:text,"zh-Hans");
  }
 }
 static BaseTranslator create(boolean ms,Transport t){return ms?new MicrosoftTranslator(t,()->t.cancelled):new DeepLTranslator(t,()->t.cancelled);}
 static void safe(Throwable e){ok(e.getCause()==null);ok(!e.toString().contains(PRIVATE));java.io.StringWriter w=new java.io.StringWriter();e.printStackTrace(new java.io.PrintWriter(w));ok(!w.toString().contains(PRIVATE));}
 static class BaseProbe extends BaseTranslator {
  int calls; String from,to;Result previous;
  protected Result translateImpl(String text,String from,String to)throws Exception {calls++;this.from=from;this.to=to;if("fail".equals(text))throw new IOException("FIXTURE_ERROR");return previous=Result.of(text,"zh-Hans");}
  protected String convertLanguageCode(String code,boolean reverse){return "zh-Hans".equals(code)&&reverse?"zh-CN":"zh-CN".equals(code)&&!reverse?"zh-Hans":code;}
  public List<String> getTargetLanguages(){return Arrays.asList("en","zh-CN");}
  Result[] batch(String[] text)throws Exception{return translateImpl(text,"zh-CN","en");}
  static String md5(String s){ok(a!=null);return a(s);}
 }
 public static void main(String[] args)throws Exception {
 switch(args[0]){
 case "result": {
  Result a=Result.of(PRIVATE,null),b=Result.of(PRIVATE,null);ok(a.translation.equals(PRIVATE)&&a.sourceLanguage==null);ok(a.equals(b)&&a.hashCode()==b.hashCode());ok(a.hashCode()==PRIVATE.hashCode());ok(!a.equals(null));ok(!a.toString().contains(PRIVATE));ok(Result.of(null,null).hashCode()==0);break;}
 case "base": {
  BaseProbe p=new BaseProbe();Result r=p.translate(PRIVATE,"zh-CN","en");ok(p.from.equals("zh-Hans")&&p.to.equals("en")&&r.sourceLanguage.equals("zh-CN")&&r!=p.previous);ok(p.supportLanguage("en")&&!p.supportLanguage("EN")&&!p.supportLanguage(null));ok(BaseProbe.md5("abc").equals("900150983cd24fb0d6963f7d28e17f72"));
  Result[] batch=p.batch(new String[]{"a","b"});ok(batch.length==2&&p.from.equals("zh-CN"));int n=p.calls;try{p.batch(new String[]{"a","fail","b"});throw new AssertionError();}catch(IOException e){ok(p.calls==n+2);}break;}
 case "closed": {
  for(BaseTranslator p:new BaseTranslator[]{new MicrosoftTranslator(),new DeepLTranslator(),MicrosoftTranslator.getInstance(),DeepLTranslator.getInstance()})try{p.translate(PRIVATE,"auto","en");throw new AssertionError();}catch(FacadeFailure e){ok(e.getMessage().equals("TRANSLATION_NOT_AUTHORIZED"));safe(e);}
  try{DeepLTranslator.setJwt(PRIVATE);throw new AssertionError();}catch(SecurityException e){safe(e);}break;}
 case "languages": {
  BaseTranslator[] p={new MicrosoftTranslator(),new DeepLTranslator()};for(int i=0;i<2;i++){List<String> expected=Arrays.asList(args[i+1].split(","));ok(p[i].getTargetLanguages().equals(expected));for(String s:expected)ok(p[i].supportLanguage(s));try{p[i].getTargetLanguages().add("XX");throw new AssertionError();}catch(UnsupportedOperationException e){}}break;}
 case "normalization": {
  for(boolean ms:new boolean[]{true,false})for(String from:new String[]{null,"","auto","zh-CN","zh-TW","ZH-cn","zh"}){
   Transport t=new Transport();Result r=create(ms,t).translate(PRIVATE,from,"zh-TW");ok(t.to.equals("zh-Hant"));String expected="zh-CN".equals(from)?"zh-Hans":"zh-TW".equals(from)?"zh-Hant":from;ok(Objects.equals(t.from,expected));ok(r.sourceLanguage.equals("zh-CN"));ok(t.seen==(ms?FixtureTransport.Provider.MICROSOFT:FixtureTransport.Provider.DEEPL));}break;}
 case "format": {
  for(boolean ms:new boolean[]{true,false})for(String text:new String[]{"",PRIVATE,"<b>𝄞 &amp; é</b>","中文\nالعربية 🇪🇸 &lt; &quot;"}){Transport t=new Transport();Result r=create(ms,t).translate(text,"auto","en");ok(r.translation.equals(text)&&t.text.equals(text)&&t.calls==1);ok(!new FixtureTransport.Response(200,PRIVATE,PRIVATE).toString().contains(PRIVATE));}break;}
 case "errors": {
  for(boolean ms:new boolean[]{true,false})for(int status:new int[]{400,403,429,456,500,504,999}){Transport t=new Transport();t.status=status;try{create(ms,t).translate(PRIVATE,"auto","en");throw new AssertionError();}catch(FacadeFailure e){safe(e);ok(e.status==(status==999?0:status)&&t.calls==1);ok(t.seen==(ms?FixtureTransport.Provider.MICROSOFT:FixtureTransport.Provider.DEEPL));}}
  for(String mode:new String[]{"io","runtime","null","invalid","tainted"}){Transport t=new Transport();t.mode=mode;try{create(true,t).translate(PRIVATE,null,"en");throw new AssertionError();}catch(FacadeFailure e){safe(e);ok(t.calls==1);}}break;}
 case "cancel": {
  Transport broken=new Transport();
  BaseTranslator guarded=new MicrosoftTranslator(broken,()->{throw new IllegalArgumentException(PRIVATE);});
  try {guarded.translate(PRIVATE,null,"en");throw new AssertionError();}catch(FacadeFailure e){safe(e);ok(broken.calls==0);}

  for(boolean ms:new boolean[]{true,false})for(String mode:new String[]{"pre","inflight","cancel","interrupt","thread"}){Transport t=new Transport();t.mode=mode;t.cancelled=mode.equals("pre");if(mode.equals("thread"))Thread.currentThread().interrupt();try{create(ms,t).translate(PRIVATE,null,"en");throw new AssertionError();}catch(CancellationException e){safe(e);ok(t.calls==((mode.equals("pre")||mode.equals("thread"))?0:1));if(mode.equals("interrupt"))ok(Thread.currentThread().isInterrupted());}finally{Thread.interrupted();}}break;}
 default:throw new AssertionError("unknown test");
 }
 System.out.println("PASS "+args[0]+"; no private values logged");
 }
}
