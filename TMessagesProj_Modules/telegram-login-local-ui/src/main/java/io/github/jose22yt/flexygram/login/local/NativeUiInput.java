package io.github.jose22yt.flexygram.login.local;
/** Ephemeral input copies. No String conversion, logging or serialization. */
public final class NativeUiInput {
    private NativeUiInput(){}
    public static char[] copy(CharSequence... parts){int length=0;for(CharSequence p:parts){if(p==null||p.length()>256-length)throw new IllegalArgumentException("LOCAL_INPUT_LIMIT");length+=p.length();}char[] out=new char[length];int n=0;for(CharSequence p:parts)for(int i=0;i<p.length();i++)out[n++]=p.charAt(i);return out;}
    public static char[] bounded(CharSequence... parts){if(parts==null)return new char[0];try{return copy(parts);}catch(IllegalArgumentException rejected){return new char[0];}}
    public static void wipe(char[] value){if(value!=null)java.util.Arrays.fill(value,'\0');}
}
