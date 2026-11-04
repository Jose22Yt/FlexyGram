/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.studio;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.drawable.BitmapDrawable;
import android.graphics.drawable.Drawable;
import android.util.Base64;
import org.telegram.messenger.ApplicationLoader;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.ActionBar.ThemeColors;
import java.io.*;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Freeze resolved colors rather than copying theme account IDs, paths or remote credentials. */
final class StudioClientTheme {
    private static final int MAX_IMAGE = 4 * 1024 * 1024;
    private StudioClientTheme() {}
    static Map<String,Object> snapshot() {
        // Finish native wallpaper loading on the worker before freezing colors or an undo receipt.
        Theme.getCachedWallpaper();
        final Drawable[] wallpaper = new Drawable[1];
        Map<String,Object> result = StudioClientBackup.onUi(() -> {
            Map<String,Object> colors = new TreeMap<>();
            for (int key=0; key<Theme.colorsCount; key++) {
                if (key == Theme.key_wallpaperFileOffset) continue;
                String name = ThemeColors.getStringName(key);
                if (name != null) colors.put(name, (long)Theme.getNonAnimatedColor(key));
            }
            Map<String,Object> values = new TreeMap<>(); values.put("colors",colors);
            String link = Theme.getStudioWallpaperLink();
            if (link != null && !link.isEmpty()) values.put("wallpaperLink",link);
            wallpaper[0] = Theme.getCachedWallpaperNonBlocking();
            return values;
        });
        if (!result.containsKey("wallpaperLink") && wallpaper[0] instanceof BitmapDrawable) {
            Bitmap bitmap = ((BitmapDrawable)wallpaper[0]).getBitmap();
            if (bitmap == null || bitmap.isRecycled()) throw new IllegalArgumentException("wallpaper_bitmap");
            byte[] bytes;
            try { bytes=encode(bitmap,Bitmap.CompressFormat.PNG); }
            catch (IllegalArgumentException largePng) { bytes=encode(bitmap,Bitmap.CompressFormat.JPEG); }
            result.put("wallpaper",Base64.encodeToString(bytes,Base64.NO_WRAP));
        }
        return result;
    }
    private static byte[] encode(Bitmap bitmap,Bitmap.CompressFormat format) {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream() {
            @Override public synchronized void write(byte[] b,int off,int len) { if((long)count+len>MAX_IMAGE)throw new IllegalArgumentException("wallpaper_size");super.write(b,off,len); }
            @Override public synchronized void write(int b) { if(count>=MAX_IMAGE)throw new IllegalArgumentException("wallpaper_size");super.write(b); }
        };
        // Native theme export also uses JPEG87. Keep PNG losslessly when it fits the bounded bundle.
        if(!bitmap.compress(format,87,bytes))throw new IllegalArgumentException("wallpaper_encode");
        return bytes.toByteArray();
    }
    static void validate(Object value) {
        Map<String,Object> theme = StudioClientBackup.object(value);
        if (!theme.containsKey("colors") || !new HashSet<>(Arrays.asList("colors","wallpaper","wallpaperLink")).containsAll(theme.keySet())
                || theme.containsKey("wallpaper") && theme.containsKey("wallpaperLink")) throw new IllegalArgumentException("theme");
        Set<String> names = new HashSet<>();
        for(int i=0;i<Theme.colorsCount;i++)if(i!=Theme.key_wallpaperFileOffset)names.add(ThemeColors.getStringName(i));
        Map<String,Object> colors = StudioClientBackup.object(theme.get("colors"));
        if(colors.isEmpty() || colors.size()>Theme.colorsCount)throw new IllegalArgumentException("theme_colors");
        for(Map.Entry<String,Object> e:colors.entrySet())if(!names.contains(e.getKey()) || !(e.getValue() instanceof Long)
                || (Long)e.getValue()<Integer.MIN_VALUE || (Long)e.getValue()>Integer.MAX_VALUE)throw new IllegalArgumentException("theme_color");
        if(theme.containsKey("wallpaperLink")) {
            Object raw=theme.get("wallpaperLink");
            if(!(raw instanceof String)||((String)raw).length()>4096||((String)raw).contains("\n")||((String)raw).contains("\r"))throw new IllegalArgumentException("wallpaper_link");
            URI uri=URI.create((String)raw);
            if(!"https".equals(uri.getScheme()) || uri.getUserInfo()!=null || !Arrays.asList("attheme.org","t.me","telegram.me").contains(uri.getHost()))throw new IllegalArgumentException("wallpaper_link");
        }
        if(theme.containsKey("wallpaper")) image(theme.get("wallpaper"));
    }
    private static byte[] image(Object raw) {
        if(!(raw instanceof String)||((String)raw).length()>((MAX_IMAGE+2)/3)*4)throw new IllegalArgumentException("wallpaper_size");
        byte[] bytes=Base64.decode((String)raw,Base64.NO_WRAP);
        BitmapFactory.Options bounds=new BitmapFactory.Options();bounds.inJustDecodeBounds=true;BitmapFactory.decodeByteArray(bytes,0,bytes.length,bounds);
        if(bytes.length>MAX_IMAGE||bounds.outWidth<1||bounds.outHeight<1||bounds.outWidth>8192||bounds.outHeight>8192||(long)bounds.outWidth*bounds.outHeight>24000000L)throw new IllegalArgumentException("wallpaper_image");
        return bytes;
    }
    static void apply(Object value) throws Exception {
        validate(value);
        Map<String,Object> theme=StudioClientBackup.object(value);
        File file=File.createTempFile("flexystudio-theme-",".attheme",ApplicationLoader.applicationContext.getCacheDir());
        try {
            try(FileOutputStream out=new FileOutputStream(file)) {
                for(Map.Entry<String,Object> color:StudioClientBackup.object(theme.get("colors")).entrySet()) {
                    // Native loader chooses image/link wallpaper only if the solid color keys are absent.
                    if((theme.containsKey("wallpaper")||theme.containsKey("wallpaperLink")) && (color.getKey().equals("chat_wallpaper")||color.getKey().startsWith("chat_wallpaper_gradient")))continue;
                    out.write((color.getKey()+"="+color.getValue()+"\n").getBytes(StandardCharsets.UTF_8));
                }
                if(theme.containsKey("wallpaperLink"))out.write(("WLS="+theme.get("wallpaperLink")+"\n").getBytes(StandardCharsets.UTF_8));
                if(theme.containsKey("wallpaper")){out.write("WPS\n".getBytes(StandardCharsets.UTF_8));out.write(image(theme.get("wallpaper")));out.write("\nWPE\n".getBytes(StandardCharsets.UTF_8));}
            }
            StudioClientBackup.onUi(() -> {if(Theme.applyStudioTheme(file)==null)throw new IOException("theme_apply");return null;});
        } finally {file.delete();}
    }
}
