/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.updates;

import java.io.*;
import java.net.URI;
import java.security.MessageDigest;
import java.util.*;

/** Staged, unreferenced policy. No networking, installer, observer, job or activation path. */
public final class FlexyUpdatePolicy {
    public static final String REPO="Jose22Yt/FlexyGram";
    public static final String PACKAGE="io.github.jose22yt.flexygram.alpha";
    public static final String CERTIFICATE="c8f04cad685ca5757d35b25ea4b0b4613c7399909948d821e6ada61f9fb12b2c";
    public static final long MAX_BYTES=512L*1024*1024;
    public enum Channel { ALPHA, BETA, STABLE }
    private FlexyUpdatePolicy(){}
    public static boolean runtimeEnabled(){return false;}
    public static final class Release {
        public final String repository,tag,commit,packageName,url,filename,sha256;
        public final Channel channel;public final long versionCode,size;public final boolean draft,prerelease;
        public Release(String repository,String tag,String commit,String packageName,Channel channel,long versionCode,long size,String filename,String url,String sha256,boolean draft,boolean prerelease){
            this.repository=repository;this.tag=tag;this.commit=commit;this.packageName=packageName;this.channel=channel;this.versionCode=versionCode;this.size=size;this.filename=filename;this.url=url;this.sha256=sha256;this.draft=draft;this.prerelease=prerelease;
        }
    }
    /** Evidence MUST originate from a cryptographic APK verifier, never a downloaded JSON boolean.
     * Android adapter intentionally absent until its signature/provenance review is complete. */
    public static final class VerifiedArchive {
        public final String packageName;public final long versionCode;public final boolean v2;
        public final Set<String> currentSignerSha256;
        public VerifiedArchive(String packageName,long versionCode,boolean v2,Set<String> signers){
            this.packageName=packageName;this.versionCode=versionCode;this.v2=v2;this.currentSignerSha256=Collections.unmodifiableSet(new HashSet<>(signers));
        }
    }
    public interface ArchiveVerifier {VerifiedArchive verify(File file)throws Exception;}
    private static boolean matches(String value,String regex){return value!=null&&value.matches(regex);}
    private static void require(boolean ok){if(!ok)throw new IllegalArgumentException("update_rejected");}
    public static void validateMetadata(Release r,Channel selected,long installedVersion,String installedPackage,String installedCertificate) {
        require(r!=null&&r.channel!=null&&selected!=null&&r.channel==selected);
        require(PACKAGE.equals(installedPackage)&&PACKAGE.equals(r.packageName));
        require(CERTIFICATE.equals(installedCertificate)&&REPO.equals(r.repository));
        require(installedVersion>=1&&installedVersion<Integer.MAX_VALUE&&r.versionCode>installedVersion&&r.versionCode<=Integer.MAX_VALUE);
        require(r.size>0&&r.size<=MAX_BYTES&&matches(r.sha256,"[0-9a-f]{64}")&&matches(r.commit,"[0-9a-f]{40}"));
        String name=selected==Channel.ALPHA?"Alpha":selected==Channel.BETA?"Beta":"Stable";
        String suffix=selected==Channel.STABLE?"":"-"+name.toLowerCase(Locale.ROOT)+"\\.[1-9][0-9]{0,9}";
        require(matches(r.tag,"v(0|[1-9][0-9]{0,3})\\.(0|[1-9][0-9]{0,3})\\.(0|[1-9][0-9]{0,3})"+suffix));
        require(!r.draft&&r.prerelease==(selected!=Channel.STABLE));
        require(("FlexyGram-"+name+"-"+r.versionCode+"-ARM64-signed.apk").equals(r.filename));
        require(r.url!=null);
        try {
            URI uri=new URI(r.url);
            require("https".equals(uri.getScheme())&&"github.com".equals(uri.getHost())&&uri.getPort()==-1&&uri.getUserInfo()==null&&uri.getRawQuery()==null&&uri.getRawFragment()==null);
            require(("/"+REPO+"/releases/download/"+r.tag+"/"+r.filename).equals(uri.getRawPath()));
        }catch(java.net.URISyntaxException invalid){throw new IllegalArgumentException("update_rejected");}
    }
    public static void validateArchive(Release r,VerifiedArchive archive) {
        require(archive!=null&&PACKAGE.equals(archive.packageName)&&r.packageName.equals(archive.packageName)&&r.versionCode==archive.versionCode);
        require(archive.v2&&archive.currentSignerSha256.equals(Collections.singleton(CERTIFICATE)));
    }
    public static void verifyDownloaded(Release r,Channel selected,long installedVersion,String installedPackage,String installedCertificate,File file,ArchiveVerifier verifier)throws Exception {
        validateMetadata(r,selected,installedVersion,installedPackage,installedCertificate);
        require(file!=null&&file.isFile()&&file.length()==r.size);
        MessageDigest digest=MessageDigest.getInstance("SHA-256");long read=0;
        try(InputStream in=new FileInputStream(file)){
            byte[] buffer=new byte[64*1024];int count;
            while((count=in.read(buffer))!=-1){if(Thread.currentThread().isInterrupted())throw new InterruptedIOException();require(count>0);read+=count;require(read<=r.size&&read<=MAX_BYTES);digest.update(buffer,0,count);}
        }
        StringBuilder hash=new StringBuilder(64);for(byte value:digest.digest()){int n=value&255;hash.append(Character.forDigit(n>>>4,16)).append(Character.forDigit(n&15,16));}
        require(read==r.size&&MessageDigest.isEqual(hash.toString().getBytes(java.nio.charset.StandardCharsets.US_ASCII),r.sha256.getBytes(java.nio.charset.StandardCharsets.US_ASCII)));
        validateArchive(r,verifier.verify(file));
        // No install here. A future adapter must keep these same private bytes immutable,
        // recheck before handing them to PackageInstaller, and require explicit user consent.
    }
}
