package app.flexygram.performance;

/** Fixed-size local counters. Durations are UI work, not end-to-end frame latency or FPS. */
public final class FrameWindowStats {
    public static final int OTHER=0, HOME=1, CHAT=2, CHAT_SCROLL=3, SETTINGS=4;
    private static final String[] NAMES={"other","home","chat","chat_scroll","settings"};
    private long invalid;
    private final long[][] values=new long[NAMES.length][4];
    public synchronized void record(int state,long uiNanos,boolean jank){
        if(state<0||state>=values.length||uiNanos<0||uiNanos>60_000_000_000L){invalid++;return;}
        long[] row=values[state];row[0]++;if(jank)row[1]++;row[2]+=uiNanos;row[3]=Math.max(row[3],uiNanos);
    }
    public synchronized String drain(){
        StringBuilder out=new StringBuilder("ui_frame_stats");
        for(int i=0;i<values.length;i++){
            long[] row=values[i];if(row[0]==0)continue;
            out.append(' ').append(NAMES[i]).append("={frames:").append(row[0]).append(",heuristic_jank:").append(row[1])
                    .append(",total_ui_ns:").append(row[2]).append(",max_ui_ns:").append(row[3]).append('}');
            java.util.Arrays.fill(row,0);
        }
        if(invalid>0){out.append(" invalid:").append(invalid);invalid=0;}
        return out.toString();
    }
    public static int state(String screen,boolean scrolling){
        if("chat".equals(screen))return scrolling?CHAT_SCROLL:CHAT;
        if("home".equals(screen))return HOME;
        if("settings".equals(screen))return SETTINGS;
        return OTHER;
    }
    public static String screen(String className){
        if("ChatActivity".equals(className))return "chat";
        if("DialogsActivity".equals(className)||"MainTabsActivity".equals(className))return "home";
        if(className!=null&&(className.endsWith("SettingsActivity")||className.equals("FlexyStudioActivity")))return "settings";
        return "other";
    }
}
