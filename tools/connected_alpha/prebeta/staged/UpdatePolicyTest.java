import app.flexygram.updates.FlexyUpdatePolicy;
import app.flexygram.updates.FlexyUpdatePolicy.*;
import java.nio.file.*;
import java.util.*;
import java.security.MessageDigest;
/** Actual staged policy; archive verifier below is a deliberate double, not APK signature verification. */
public class UpdatePolicyTest {
 static int count;
 static void check(boolean ok){count++;if(!ok)throw new AssertionError("case"+count);}
 static void reject(Runnable action){try{action.run();throw new AssertionError("accepted untrusted update");}catch(IllegalArgumentException expected){count++;}}
 static String hash(byte[] bytes)throws Exception{StringBuilder b=new StringBuilder();for(byte x:MessageDigest.getInstance("SHA-256").digest(bytes))b.append(String.format("%02x",x&255));return b.toString();}
 static Release release(String repo,Channel channel,long version,String tag,String url,String checksum,long size,boolean draft,boolean prerelease){return new Release(repo,tag,"a".repeat(40),FlexyUpdatePolicy.PACKAGE,channel,version,size,"FlexyGram-"+(channel==Channel.STABLE?"Stable":channel==Channel.ALPHA?"Alpha":"Beta")+"-"+version+"-ARM64-signed.apk",url,checksum,draft,prerelease);}
 static String url(Channel c,long version,String tag){return "https://github.com/Jose22Yt/FlexyGram/releases/download/"+tag+"/FlexyGram-"+(c==Channel.ALPHA?"Alpha":c==Channel.BETA?"Beta":"Stable")+"-"+version+"-ARM64-signed.apk";}
 static void validate(Release r,Channel selected){FlexyUpdatePolicy.validateMetadata(r,selected,1274,FlexyUpdatePolicy.PACKAGE,FlexyUpdatePolicy.CERTIFICATE);}
 public static void main(String[] args)throws Exception{
  check(!FlexyUpdatePolicy.runtimeEnabled());byte[] bytes="synthetic policy input, not an APK".getBytes(java.nio.charset.StandardCharsets.UTF_8);String sha=hash(bytes);
  for(Channel channel:Channel.values()){
   String tag="v1.0.0"+(channel==Channel.STABLE?"":"-"+channel.name().toLowerCase()+".1275");Release valid=release(FlexyUpdatePolicy.REPO,channel,1275,tag,url(channel,1275,tag),sha,bytes.length,false,channel!=Channel.STABLE);
   validate(valid,channel);check(true);
   for(Channel other:Channel.values())if(other!=channel)reject(()->validate(valid,other));
   reject(()->FlexyUpdatePolicy.validateMetadata(valid,channel,1275,FlexyUpdatePolicy.PACKAGE,FlexyUpdatePolicy.CERTIFICATE));
   reject(()->FlexyUpdatePolicy.validateMetadata(valid,channel,1276,FlexyUpdatePolicy.PACKAGE,FlexyUpdatePolicy.CERTIFICATE));
   reject(()->FlexyUpdatePolicy.validateMetadata(valid,channel,1274,"com.exteraless.app",FlexyUpdatePolicy.CERTIFICATE));
   reject(()->FlexyUpdatePolicy.validateMetadata(valid,channel,1274,FlexyUpdatePolicy.PACKAGE,"b".repeat(64)));
   for(String bad:new String[]{"http://github.com/Jose22Yt/FlexyGram/releases/download/"+tag+"/"+valid.filename,valid.url+"?token=untrusted",valid.url+"#x",valid.url.replace("github.com","github.com.evil.invalid"),valid.url.replace("github.com/","github.com:443/"),valid.url.replace("github.com/","name@github.com/"),valid.url.replace("Jose22Yt/FlexyGram","exteraless/exteraless"),valid.url.replace("releases/download/","releases/download/%2e%2e/"),null})reject(()->validate(release(FlexyUpdatePolicy.REPO,channel,1275,tag,bad,sha,bytes.length,false,channel!=Channel.STABLE),channel));
   for(String repo:new String[]{"exteraless/exteraless","Jose22Yt/FlexyGram-fake",null})reject(()->validate(release(repo,channel,1275,tag,valid.url,sha,bytes.length,false,channel!=Channel.STABLE),channel));
   for(long size:new long[]{0,-1,FlexyUpdatePolicy.MAX_BYTES+1})reject(()->validate(release(FlexyUpdatePolicy.REPO,channel,1275,tag,valid.url,sha,size,false,channel!=Channel.STABLE),channel));
   reject(()->validate(release(FlexyUpdatePolicy.REPO,channel,1275,tag,valid.url,sha,bytes.length,true,channel!=Channel.STABLE),channel));
   reject(()->validate(release(FlexyUpdatePolicy.REPO,channel,1275,tag,valid.url,sha,bytes.length,false,channel==Channel.STABLE),channel));
   for(String bad:new String[]{"v1.0.0-rc.1275","v1.0.0/../alpha","1.0.0-alpha.1275",null})reject(()->validate(release(FlexyUpdatePolicy.REPO,channel,1275,bad,valid.url,sha,bytes.length,false,channel!=Channel.STABLE),channel));
   VerifiedArchive evidence=new VerifiedArchive(FlexyUpdatePolicy.PACKAGE,1275,true,Set.of(FlexyUpdatePolicy.CERTIFICATE));FlexyUpdatePolicy.validateArchive(valid,evidence);check(true);
   for(VerifiedArchive bad:new VerifiedArchive[]{new VerifiedArchive("com.exteraless.app",1275,true,Set.of(FlexyUpdatePolicy.CERTIFICATE)),new VerifiedArchive(FlexyUpdatePolicy.PACKAGE,1274,true,Set.of(FlexyUpdatePolicy.CERTIFICATE)),new VerifiedArchive(FlexyUpdatePolicy.PACKAGE,1275,false,Set.of(FlexyUpdatePolicy.CERTIFICATE)),new VerifiedArchive(FlexyUpdatePolicy.PACKAGE,1275,true,Set.of("b".repeat(64))),new VerifiedArchive(FlexyUpdatePolicy.PACKAGE,1275,true,Set.of(FlexyUpdatePolicy.CERTIFICATE,"b".repeat(64)))})reject(()->FlexyUpdatePolicy.validateArchive(valid,bad));
   Path fixture=Files.createTempFile("flexy-policy-",".bin");try{Files.write(fixture,bytes);FlexyUpdatePolicy.verifyDownloaded(valid,channel,1274,FlexyUpdatePolicy.PACKAGE,FlexyUpdatePolicy.CERTIFICATE,fixture.toFile(),f->evidence);check(true);Files.write(fixture,"tampered".getBytes());try{FlexyUpdatePolicy.verifyDownloaded(valid,channel,1274,FlexyUpdatePolicy.PACKAGE,FlexyUpdatePolicy.CERTIFICATE,fixture.toFile(),f->evidence);throw new AssertionError();}catch(IllegalArgumentException expected){count++;}}finally{Files.delete(fixture);}
  }
  System.out.println("PASS staged policy checks="+count+"; archive evidence is a double; runtime DISABLED; Android integration NOT_TESTED");
 }
}
