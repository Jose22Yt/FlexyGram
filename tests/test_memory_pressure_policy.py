"""Background visibility isn't memory pressure; exercise actual callbacks and cache code."""
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method

CONSTANTS='package android.content;public interface ComponentCallbacks2{int TRIM_MEMORY_RUNNING_LOW=10,TRIM_MEMORY_RUNNING_CRITICAL=15,TRIM_MEMORY_UI_HIDDEN=20,TRIM_MEMORY_COMPLETE=80;}'


def test_ui_hidden_does_not_cold_start_every_cache_and_pressure_still_releases(tmp_path):
    src=(JAVA/'org/telegram/messenger/ApplicationLoader.java').read_text()
    methods='\n'.join(method(src,s) for s in ['public void onTrimMemory(', 'public void onLowMemory()'])
    probe(tmp_path,{
      'android/content/ComponentCallbacks2.java':CONSTANTS,
      'app/flexygram/bubbles/SignatureWallpaperBlur.java':'package app.flexygram.bubbles;public class SignatureWallpaperBlur{public static int calls;public static void trimMemory(int l){calls++;}}',
      'app/flexygram/performance/TextLayoutPrecompute.java':'package app.flexygram.performance;public class TextLayoutPrecompute{public static int calls;public static void trimMemory(int l){calls++;}}',
      'org/telegram/messenger/MessagesStorage.java':'package org.telegram.messenger;public class MessagesStorage{public static int calls;public static void trimWarmHistories(){calls++;}}',
      'org/telegram/messenger/ImageLoader.java':'''package org.telegram.messenger;public class ImageLoader{
public static int starts,trims,clears;public static ImageLoader getInstance(){starts++;return new ImageLoader();}
public void clearMemory(){clears++;}public static void trimMemory(int l){trims++;}}''',
      'Probe.java':'''import org.telegram.messenger.*;
class Parent{public void onTrimMemory(int l){}public void onLowMemory(){}}
public class Probe extends Parent{
 METHODS
 static void check(boolean b){if(!b)throw new AssertionError("UI_HIDDEN must not evict caches or initialize the image loader");}
 public static void main(String[]args){Probe p=new Probe();for(int i=0;i<10000;i++)p.onTrimMemory(20);
 check(ImageLoader.starts==0&&ImageLoader.clears==0&&ImageLoader.trims==0);
 check(MessagesStorage.calls==0&&app.flexygram.bubbles.SignatureWallpaperBlur.calls==0&&app.flexygram.performance.TextLayoutPrecompute.calls==0);
 p.onTrimMemory(10);check(ImageLoader.trims==1&&MessagesStorage.calls==1);
 p.onLowMemory();check(ImageLoader.trims==2&&ImageLoader.starts==0&&MessagesStorage.calls==2);
 }}'''.replace('METHODS',methods)
    })


def test_real_image_caches_evict_old_entries_only_under_pressure_without_changing_budget(tmp_path):
    src=(JAVA/'org/telegram/messenger/ImageLoader.java').read_text()
    methods='\n'.join(method(src,s) for s in ['public static void trimMemory(', 'public void clearMemory()'])
    probe(tmp_path,{
      'android/content/ComponentCallbacks2.java':CONSTANTS,
      'Probe.java':'''import org.telegram.messenger.LruCache;
class ImageLoader{
 static ImageLoader Instance;
 final LruCache<String> smallImagesMemCache=new LruCache<>(8),memCache=new LruCache<>(8),wallpaperMemCache=new LruCache<>(8),lottieMemCache=new LruCache<>(8);
 static class Stripped extends LruCache<String>{Stripped(){super(8);}void trimToSize(int n){evictToSize(n);}}
 static final Stripped inu_strippedCache=new Stripped();
 METHODS
}
public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){
 for(int i=0;i<8;i++)ImageLoader.inu_strippedCache.put("pre@"+i,"v");
 ImageLoader.trimMemory(10);check(ImageLoader.Instance==null&&ImageLoader.inu_strippedCache.size()==4);
 ImageLoader.trimMemory(15);check(ImageLoader.Instance==null&&ImageLoader.inu_strippedCache.size()==0);
 ImageLoader l=ImageLoader.Instance=new ImageLoader();LruCache<String>[] caches=new LruCache[]{l.smallImagesMemCache,l.memCache,l.wallpaperMemCache,l.lottieMemCache,ImageLoader.inu_strippedCache};
 for(int round=0;round<1000;round++){
  for(var c:caches){for(int i=0;i<8;i++)c.put("image@"+i,"v");c.moveToFront("image@0");}
  ImageLoader.trimMemory(20);for(var c:caches)check(c.size()==8);
  ImageLoader.trimMemory(5);for(var c:caches)check(c.size()==8);
  ImageLoader.trimMemory(10);for(var c:caches)check(c.size()==4&&c.maxSize()==8&&c.get("image@0")!=null&&c.get("image@1")==null);
  ImageLoader.trimMemory(round%2==0?15:80);for(var c:caches)check(c.size()==0&&c.maxSize()==8);
 }
 try{l.memCache.evictToSize(-1);throw new AssertionError();}catch(IllegalArgumentException expected){}
 }}'''.replace('METHODS',methods)
    },[JAVA/'org/telegram/messenger/LruCache.java'])
