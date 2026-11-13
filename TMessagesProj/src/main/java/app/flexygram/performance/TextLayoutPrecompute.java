package app.flexygram.performance;

import android.os.Build;
import android.text.Layout;
import android.text.PrecomputedText;
import android.text.Spanned;
import android.text.TextDirectionHeuristics;
import android.text.TextPaint;
import androidx.annotation.RequiresApi;
import java.util.*;
import java.util.concurrent.*;

/** Bounded, opportunistic metrics for span-free text. Misses never wait for a worker.
 * No message/account identifiers, shared Paints, views, persistence or background draw loops. */
public final class TextLayoutPrecompute {
    private static volatile boolean used;
    private TextLayoutPrecompute() { }

    public static CharSequence getOrSchedule(CharSequence text, TextPaint paint) {
        if (Build.VERSION.SDK_INT < 28 || text == null || text.length() < 160 || text.length() > 8192) return text;
        if (android.os.Looper.myLooper() != android.os.Looper.getMainLooper()) return text;
        if (!(text instanceof String) && !(text instanceof Spanned)) return text;
        // ReplacementSpan, emoji, spoilers and any mutable/custom span stay on their native path.
        if (text instanceof Spanned && ((Spanned) text).getSpans(0, text.length(), Object.class).length != 0) return text;
        used = true;
        return Api28.getOrSchedule(text, paint);
    }

    public static void trimMemory(int level) {
        if (Build.VERSION.SDK_INT >= 28 && used && level >= 10) Api28.clear();
    }

    @RequiresApi(28)
    private static final class Api28 {
        private static final int MAX_ENTRIES = 32, MAX_CHARACTERS = 32768;
        private static final LinkedHashMap<Key,PrecomputedText> ready = new LinkedHashMap<>(16,.75f,true);
        private static final Map<Key,Long> pending = new HashMap<>();
        private static final ThreadPoolExecutor worker = new ThreadPoolExecutor(0,1,1,TimeUnit.SECONDS,
                new ArrayBlockingQueue<>(2),r->{Thread t=new Thread(()->{android.os.Process.setThreadPriority(android.os.Process.THREAD_PRIORITY_BACKGROUND);r.run();},"FlexyTextMetrics");t.setDaemon(true);return t;},new ThreadPoolExecutor.AbortPolicy());
        private static int characters;
        private static long generation;
        private static final class Key {
            final String text; final PrecomputedText.Params params;
            Key(String text,TextPaint paint) {
                this.text=text;
                params=new PrecomputedText.Params.Builder(paint)
                        .setBreakStrategy(Layout.BREAK_STRATEGY_HIGH_QUALITY)
                        .setHyphenationFrequency(Layout.HYPHENATION_FREQUENCY_NONE)
                        .setTextDirection(TextDirectionHeuristics.FIRSTSTRONG_LTR).build();
            }
            @Override public boolean equals(Object other){return other instanceof Key&&text.equals(((Key)other).text)&&params.equals(((Key)other).params);}
            @Override public int hashCode(){return 31*text.hashCode()+params.hashCode();}
        }
        static CharSequence getOrSchedule(CharSequence original,TextPaint paint) {
            Key key=new Key(original instanceof String ? (String) original : original.toString(),paint);
            final long token;
            synchronized (ready) {
                PrecomputedText hit=ready.get(key);
                if(hit!=null)return hit;
                if(pending.containsKey(key)||pending.size()>=3)return original;
                token=generation;pending.put(key,token);
            }
            try {worker.execute(()->{
                PrecomputedText result=null;
                try {result=PrecomputedText.create(key.text,key.params);}catch(RuntimeException|OutOfMemoryError unavailable){ /* Native layout remains the fallback. */ }
                synchronized (ready) {
                    pending.remove(key,token);
                    if(token!=generation||result==null)return;
                    PrecomputedText old=ready.put(key,result);
                    if(old==null)characters+=key.text.length();
                    Iterator<Map.Entry<Key,PrecomputedText>> iterator=ready.entrySet().iterator();
                    while((ready.size()>MAX_ENTRIES||characters>MAX_CHARACTERS)&&iterator.hasNext()){
                        characters-=iterator.next().getKey().text.length();iterator.remove();
                    }
                }
            });}catch(RejectedExecutionException full){synchronized(ready){pending.remove(key,token);}}
            return original;
        }
        static void clear(){synchronized(ready){generation++;ready.clear();characters = 0;pending.clear();worker.getQueue().clear();characters=0;}}
    }
}
