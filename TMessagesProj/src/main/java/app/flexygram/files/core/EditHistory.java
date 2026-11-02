/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.files.core;
import java.util.ArrayDeque;
/** Delta history with independent count/character budgets. No document snapshots per key. */
public final class EditHistory {
    public static final class Change {public final int start;public final String before,after;Change(int s,String b,String a){start=s;before=b;after=a;}}
    private final ArrayDeque<Change> undo=new ArrayDeque<>(),redo=new ArrayDeque<>();private int retained;
    private int cost(Change c){return c.before.length()+c.after.length();}
    public void record(int start,String before,String after){for(Change c:redo)retained-=cost(c);redo.clear();Change c=new Change(start,before,after);undo.addLast(c);retained+=cost(c);while(undo.size()>64||retained>512*1024){retained-=cost(undo.removeFirst());}}
    public Change undo(){if(undo.isEmpty())return null;Change c=undo.removeLast();redo.addLast(c);return c;}
    public Change redo(){if(redo.isEmpty())return null;Change c=redo.removeLast();undo.addLast(c);return c;}
    public void clear(){undo.clear();redo.clear();retained=0;}
    public int retainedChars(){return retained;}
}
