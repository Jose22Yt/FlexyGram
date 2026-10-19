import lab.flexygram.translation.PrototypeAdapter;
import lab.flexygram.translation.PrototypeAdapter.*;
import app.nekogram.translator.BaseTranslator;
import java.util.*;
import java.io.IOException;
import java.util.concurrent.CancellationException;

/** Executes BaseTranslator only, never Microsoft/DeepL/Google implementations or singletons. */
public class ParityHarness {
    static final String PRIVATE="SYNTHETIC_PRIVATE_🔒_TEXT<em>hola</em>\nURL_KEY_RESPONSE_NOT_REAL";
    static int calls; static Request last; static boolean cancelled;
    static void ok(boolean condition){if(!condition)throw new AssertionError("PARITY_ASSERTION");}
    static class Oracle extends BaseTranslator {
        final List<String> languages; String from,to,query;
        Oracle(List<String> languages){this.languages=languages;}
        public List<String> getTargetLanguages(){return languages;}
        protected String convertLanguageCode(String s,boolean reverse){
            if(s==null)return null;
            if(reverse){if(s.equals("zh-Hans"))return "zh-CN";if(s.equals("zh-Hant"))return "zh-TW";}
            else {if(s.equals("zh-CN"))return "zh-Hans";if(s.equals("zh-TW"))return "zh-Hant";}
            return s;
        }
        protected app.nekogram.translator.Result translateImpl(String text,String source,String target){
            query=text;from=source;to=target;return app.nekogram.translator.Result.of(text,"zh-Hans");
        }
    }
    static PrototypeAdapter adapter(Provider p,FixtureTransport t){return new PrototypeAdapter(p,Set.of("en","es","zh-CN","zh-TW","pt-BR","en-US"),t);}
    static Response echo(Request r,Cancellation c){calls++;last=r;return new Response(200,r.text(),"zh-Hans");}
    static void failure(PrototypeAdapter a,int status,String code) throws Exception {
        try{a.translate(PRIVATE,"auto","es",Format.TEXT,Formality.DEFAULT,()->false);throw new AssertionError();}
        catch(Failure f){ok(f.status==status&&f.getMessage().equals(code)&&f.getCause()==null&&!f.toString().contains(PRIVATE));}
    }
    public static void main(String[] args)throws Exception {
        switch(args[0]){
            case "base": {
                Oracle o=new Oracle(List.of("es","zh-CN"));
                var r=o.translate(PRIVATE,"zh-TW","zh-CN");
                ok(o.query.equals(PRIVATE)&&o.from.equals("zh-Hant")&&o.to.equals("zh-Hans"));
                ok(r.translation.equals(PRIVATE)&&r.sourceLanguage.equals("zh-CN"));
                ok(r.equals(app.nekogram.translator.Result.of(PRIVATE,"zh-CN")));
                o.translate("","auto","es");ok(o.query.isEmpty()&&o.from.equals("auto"));
                break;
            }
            case "languages": {
                for(int i=1;i<args.length;i++){
                    var list=List.of(args[i].split(","));Oracle o=new Oracle(list);
                    var a=new PrototypeAdapter(i==1?Provider.MICROSOFT:Provider.DEEPL,new HashSet<>(list),ParityHarness::echo);
                    for(String l:list)ok(o.supportLanguage(l)==a.supportLanguage(l));
                    ok(!a.supportLanguage(null)&&!a.supportLanguage("zz-INVALID"));
                }break;
            }
            case "normalization": {
                for(Provider p:Provider.values())for(String s:new String[]{null,"auto","","zh-CN","zh-TW","ZH-CN","es","pt-BR"}){
                    Oracle o=new Oracle(List.of("es"));o.translate(PRIVATE,p==Provider.MICROSOFT&&"auto".equals(s)?null:s,"es");
                    adapter(p,ParityHarness::echo).translate(PRIVATE,s,"es",Format.TEXT,Formality.DEFAULT,()->false);
                    ok(Objects.equals(o.from,last.source())&&Objects.equals(o.to,last.target()));
                }break;
            }
            case "aliases": {
                for(String t:new String[]{"zh","zh-cn","zh-hans","ZH-CN","zh-tw","zh-hk","zh-hant"}){
                    adapter(Provider.MICROSOFT,ParityHarness::echo).translate(PRIVATE,"auto",t,Format.TEXT,Formality.DEFAULT,()->false);
                    ok(last.target().equals(t.toLowerCase(Locale.ROOT).matches("zh-tw|zh-hk|zh-hant")?"zh-Hant":"zh-Hans"));
                }break;
            }
            case "format": {
                for(Provider p:Provider.values())for(Format f:Format.values()){
                    var r=adapter(p,ParityHarness::echo).translate(PRIVATE,"auto","es",f,Formality.DEFAULT,()->false);
                    ok(r.translation().equals(PRIVATE)&&r.sourceLanguage().equals("zh-CN")&&last.format()==f);
                    ok(!r.toString().contains(PRIVATE)&&!last.toString().contains(PRIVATE));
                }break;
            }
            case "formality": {
                for(Formality f:Formality.values()){
                    adapter(Provider.DEEPL,ParityHarness::echo).translate(PRIVATE,"auto","es",Format.HTML,f,()->false);ok(last.formality()==f);
                }
                int before=calls;
                try{adapter(Provider.MICROSOFT,ParityHarness::echo).translate(PRIVATE,"auto","es",Format.TEXT,Formality.PREFER_MORE,()->false);throw new AssertionError();}
                catch(Failure f){ok(f.getMessage().equals("UNSUPPORTED_FORMALITY")&&calls==before);}break;
            }
            case "errors": {
                for(Provider p:Provider.values())for(int status:new int[]{400,403,429,456,500,504}){
                    int before=calls;failure(adapter(p,(r,c)->{calls++;return new Response(status,PRIVATE,PRIVATE);}),status,"PROVIDER_HTTP_ERROR");ok(calls==before+1);
                }
                failure(adapter(Provider.DEEPL,(r,c)->{throw new IOException(PRIVATE);}),0,"PROVIDER_FAILED");
                failure(adapter(Provider.DEEPL,(r,c)->null),0,"INVALID_RESPONSE");break;
            }
            case "cancel": {
                try{adapter(Provider.MICROSOFT,ParityHarness::echo).translate(PRIVATE,"auto","es",Format.TEXT,Formality.DEFAULT,()->true);throw new AssertionError();}catch(CancellationException e){ok(calls==0);}
                try{adapter(Provider.DEEPL,(r,c)->{calls++;cancelled=true;return new Response(200,PRIVATE,"es");}).translate(PRIVATE,"auto","es",Format.TEXT,Formality.DEFAULT,()->cancelled);throw new AssertionError();}catch(CancellationException e){ok(calls==1&&!e.toString().contains(PRIVATE));}
                try{adapter(Provider.DEEPL,(r,c)->{throw new CancellationException(PRIVATE);}).translate(PRIVATE,"auto","es",Format.TEXT,Formality.DEFAULT,()->false);throw new AssertionError();}catch(CancellationException e){ok(!e.toString().contains(PRIVATE));}
                try{adapter(Provider.DEEPL,(r,c)->{throw new InterruptedException(PRIVATE);}).translate(PRIVATE,"auto","es",Format.TEXT,Formality.DEFAULT,()->false);throw new AssertionError();}catch(CancellationException e){ok(Thread.currentThread().isInterrupted());}finally{Thread.interrupted();}break;
            }
            case "invalid": {
                try{adapter(Provider.MICROSOFT,ParityHarness::echo).translate(PRIVATE,"auto","zz-INVALID",Format.TEXT,Formality.DEFAULT,()->false);throw new AssertionError();}catch(Failure e){ok(calls==0);}
                try{new PrototypeAdapter(Provider.DEEPL,Set.of("es"),null);throw new AssertionError();}catch(NullPointerException expected){}break;
            }
            default:throw new AssertionError("UNKNOWN_CASE");
        }
        System.out.println("PASS "+args[0]+"; fake transport only");
    }
}
