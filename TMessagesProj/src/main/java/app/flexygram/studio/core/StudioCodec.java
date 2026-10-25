/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.studio.core;

import java.io.*;
import java.nio.*;
import java.nio.charset.*;
import java.security.*;
import java.util.*;

/** Bounded UTF-8 data only. No ZIPs, classes, URIs, reflection, code or preference access. */
public final class StudioCodec {
    private static final String FORMAT="FlexyGram.NativeSettings";
    public static final class Preset {
        public final String name;
        public final int minApp;
        public final Map<String,Map<String,Object>> sections;
        private Preset(String name,int minApp,Map<String,Map<String,Object>> input) {
            if(!StudioSchema.filename(name)||minApp<StudioSchema.MIN_APP)throw new IllegalArgumentException("metadata");
            this.name=name;this.minApp=minApp;
            Map<String,Map<String,Object>> copy=new TreeMap<>();int count=0;
            for(Map.Entry<String,Map<String,Object>> section:input.entrySet()) {
                if(!StudioSchema.sections().contains(section.getKey()))throw new StudioSchema.Unsupported(section.getKey());
                if(section.getValue().isEmpty())throw new IllegalArgumentException("section");
                Map<String,Object> values=new TreeMap<>();
                for(Map.Entry<String,Object> entry:section.getValue().entrySet()) {
                    StudioSchema.Key key=StudioSchema.key(section.getKey(),entry.getKey());
                    values.put(key.id,StudioSchema.value(key,entry.getValue()));
                    if(++count>StudioSchema.MAX_KEYS)throw new IllegalArgumentException("keys");
                }
                copy.put(section.getKey(),Collections.unmodifiableMap(values));
            }
            if(copy.isEmpty())throw new IllegalArgumentException("empty");
            sections=Collections.unmodifiableMap(copy);
        }
    }
    private StudioCodec(){}
    public static Preset create(String name,Map<String,Map<String,Object>> values){return new Preset(name,StudioSchema.MIN_APP,values);}
    public static Preset export(String name,Map<String,Map<String,Object>> snapshot,Set<String> explicitlyIncluded) {
        Map<String,Map<String,Object>> result=new TreeMap<>();
        for(String section:snapshot.keySet()) {
            Map<String,Object> values=new TreeMap<>();
            for(Map.Entry<String,Object> entry:snapshot.get(section).entrySet()) {
                StudioSchema.Key key=StudioSchema.key(section,entry.getKey());Object v=StudioSchema.value(key,entry.getValue());
                if(explicitlyIncluded.contains(section)||!key.defaultValue.equals(v))values.put(key.id,v);
            }
            if(!values.isEmpty())result.put(section,values);
        }
        for(String section:explicitlyIncluded)if(!StudioSchema.sections().contains(section))throw new IllegalArgumentException("section");
        return create(name,result);
    }
    public static byte[] readLimited(InputStream in)throws IOException {
        ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buffer=new byte[4096];int count;
        while((count=in.read(buffer))!=-1) {
            if(Thread.currentThread().isInterrupted())throw new InterruptedIOException();
            if(count==0)throw new IOException("stream");
            if(out.size()+count>StudioSchema.MAX_BYTES)throw new IOException("size");out.write(buffer,0,count);
        }
        return out.toByteArray();
    }
    public static byte[] encode(Preset preset) {
        String payload=payload(preset);String document=payload.substring(0,payload.length()-1)+",\"sha256\":"+quote(hash(payload.getBytes(StandardCharsets.UTF_8)))+"}";
        byte[] bytes=document.getBytes(StandardCharsets.UTF_8);
        if(bytes.length>StudioSchema.MAX_BYTES)throw new IllegalArgumentException("size");return bytes;
    }
    @SuppressWarnings("unchecked")
    public static Preset decode(byte[] data,int appVersion) {
        if(data.length==0||data.length>StudioSchema.MAX_BYTES)throw new IllegalArgumentException("size");
        final String text;
        try{text=StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(data)).toString();}
        catch(CharacterCodingException invalid){throw new IllegalArgumentException("utf8");}
        Object root=new Parser(text).parse();
        if(!(root instanceof Map))throw new IllegalArgumentException("format");Map<String,Object> map=(Map<String,Object>)root;
        if(!map.keySet().equals(new HashSet<>(Arrays.asList("format","schema","minApp","name","sections","sha256")))||!FORMAT.equals(map.get("format"))||!Long.valueOf(1).equals(map.get("schema")))throw new IllegalArgumentException("schema");
        if(!(map.get("minApp") instanceof Long))throw new IllegalArgumentException("version");
        long minimum=(Long)map.get("minApp");if(minimum>appVersion)throw new StudioSchema.Unsupported("minApp="+minimum);
        if(minimum<StudioSchema.MIN_APP||minimum>Integer.MAX_VALUE)throw new IllegalArgumentException("version");
        if(!(map.get("name") instanceof String)||!(map.get("sections") instanceof List))throw new IllegalArgumentException("metadata");
        Map<String,Map<String,Object>> sections=new TreeMap<>();List<?> list=(List<?>)map.get("sections");
        if(list.size()>StudioSchema.sections().size())throw new IllegalArgumentException("sections");
        for(Object item:list) {
            if(!(item instanceof Map))throw new IllegalArgumentException("section");Map<String,Object> section=(Map<String,Object>)item;
            if(!section.keySet().equals(new HashSet<>(Arrays.asList("id","values")))||!(section.get("id") instanceof String)||!(section.get("values") instanceof Map))throw new IllegalArgumentException("section");
            String id=(String)section.get("id");if(sections.put(id,(Map<String,Object>)section.get("values"))!=null)throw new IllegalArgumentException("duplicate_section");
        }
        Preset preset=new Preset((String)map.get("name"),(int)minimum,sections);
        String digest=map.get("sha256") instanceof String?(String)map.get("sha256"):"";
        if(!digest.matches("[0-9a-f]{64}")||!MessageDigest.isEqual(digest.getBytes(StandardCharsets.US_ASCII),hash(payload(preset).getBytes(StandardCharsets.UTF_8)).getBytes(StandardCharsets.US_ASCII)))throw new IllegalArgumentException("integrity");
        return preset;
    }
    private static String payload(Preset p) {
        StringBuilder b=new StringBuilder("{\"format\":").append(quote(FORMAT)).append(",\"schema\":1,\"minApp\":").append(p.minApp).append(",\"name\":").append(quote(p.name)).append(",\"sections\":[");
        boolean first=true;
        for(Map.Entry<String,Map<String,Object>> section:p.sections.entrySet()) {
            if(!first)b.append(',');first=false;b.append("{\"id\":").append(quote(section.getKey())).append(",\"values\":{");boolean one=true;
            for(Map.Entry<String,Object> entry:section.getValue().entrySet()) {
                if(!one)b.append(',');one=false;b.append(quote(entry.getKey())).append(':');Object value=entry.getValue();
                b.append(value instanceof String?quote((String)value):value.toString());
            }
            b.append("}}");
        }
        return b.append("]}").toString();
    }
    private static String hash(byte[] bytes) {
        try{byte[] digest=MessageDigest.getInstance("SHA-256").digest(bytes);char[] out=new char[digest.length*2];String hex="0123456789abcdef";for(int i=0;i<digest.length;i++){int v=digest[i]&255;out[i*2]=hex.charAt(v>>>4);out[i*2+1]=hex.charAt(v&15);}return new String(out);}
        catch(NoSuchAlgorithmException impossible){throw new AssertionError(impossible);}
    }
    private static String quote(String text) {
        StringBuilder out=new StringBuilder("\"");
        for(int i=0;i<text.length();i++){char c=text.charAt(i);if(c=='"'||c=='\\')out.append('\\');if(c<32)throw new IllegalArgumentException("string");out.append(c);}
        return out.append('"').toString();
    }
    /** Small strict JSON grammar: integral values only, duplicates/depth/tokens/strings bounded. */
    private static final class Parser {
        final String s;int at,nodes;
        Parser(String s){this.s=s;}
        Object parse(){Object result=value(0);ws();if(at!=s.length())fail();return result;}
        void ws(){while(at<s.length()&&(s.charAt(at)==' '||s.charAt(at)=='\n'||s.charAt(at)=='\r'||s.charAt(at)=='\t'))at++;}
        boolean take(char c){ws();if(at<s.length()&&s.charAt(at)==c){at++;return true;}return false;}
        Object value(int depth){
            if(depth>6||++nodes>256)fail();ws();if(at>=s.length())fail();char c=s.charAt(at);
            if(c=='{') {at++;Map<String,Object> result=new LinkedHashMap<>();if(take('}'))return result;
                do{ws();String key=string();if(!take(':')||result.containsKey(key))fail();result.put(key,value(depth+1));}while(take(','));if(!take('}'))fail();return result;}
            if(c=='['){at++;List<Object> result=new ArrayList<>();if(take(']'))return result;do{result.add(value(depth+1));}while(take(','));if(!take(']'))fail();return result;}
            if(c=='"')return string();
            for(String lit:Arrays.asList("true","false"))if(s.startsWith(lit,at)){at+=lit.length();return lit.equals("true");}
            int start=at;if(c=='-')at++;if(at>=s.length()||!Character.isDigit(s.charAt(at))||s.charAt(at)>'9')fail();
            if(s.charAt(at)=='0')at++;else while(at<s.length()&&s.charAt(at)>='0'&&s.charAt(at)<='9')at++;
            if(at-start>12)fail();try{return Long.parseLong(s.substring(start,at));}catch(NumberFormatException invalid){fail();return null;}
        }
        String string(){
            if(at>=s.length()||s.charAt(at++)!='"')fail();StringBuilder out=new StringBuilder();boolean done=false;
            while(at<s.length()) {char c=s.charAt(at++);if(c=='"'){done=true;break;}if(c<32)fail();
                if(c=='\\'){if(at>=s.length())fail();c=s.charAt(at++);if(c=='u'){if(at+4>s.length())fail();try{c=(char)Integer.parseInt(s.substring(at,at+4),16);}catch(NumberFormatException e){fail();}at+=4;}
                    else if(c=='n')c='\n';else if(c=='r')c='\r';else if(c=='t')c='\t';else if(c=='b')c='\b';else if(c=='f')c='\f';else if(c!='"'&&c!='\\'&&c!='/')fail();}
                out.append(c);if(out.length()>256)fail();
            }
            if(!done)fail();String value=out.toString();
            for(int i=0;i<value.length();i++){char c=value.charAt(i);if(Character.isHighSurrogate(c)){if(++i>=value.length()||!Character.isLowSurrogate(value.charAt(i)))fail();}else if(Character.isLowSurrogate(c))fail();}
            return value;
        }
        void fail(){throw new IllegalArgumentException("malformed");}
    }
}
