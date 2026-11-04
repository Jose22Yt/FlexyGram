/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.studio.core;

import java.io.*;
import java.nio.ByteBuffer;
import java.nio.charset.*;
import java.util.*;

/** Versioned rollback journal; v2 replaces writeUTF's 64KB limit for complete client snapshots. */
public final class StudioJournal {
    private static final int V1=0x46534731,V2=0x46534732;
    private StudioJournal() {}
    public static Map<StudioSchema.Key,StudioTransaction.Slot> read(InputStream stream,long size)throws IOException {
        if(size<8||size>StudioSchema.MAX_BYTES+16384)throw new IOException("journal_size");
        DataInputStream in=new DataInputStream(stream);
        int magic=in.readInt();if(magic!=V1&&magic!=V2)throw new IOException("journal_version");
        int count=in.readInt();if(count<1||count>StudioSchema.MAX_KEYS)throw new IOException("journal_count");
        Map<StudioSchema.Key,StudioTransaction.Slot> result=new LinkedHashMap<>();
        try {
            for(int i=0;i<count;i++) {
                StudioSchema.Key key=StudioSchema.key(in.readUTF(),in.readUTF());
                boolean present=in.readBoolean();Object value;
                if(key.defaultValue instanceof Boolean)value=in.readBoolean();
                else if(key.defaultValue instanceof Integer)value=in.readInt();
                else if(magic==V1)value=in.readUTF();
                else {
                    int length=in.readInt();if(length<0||length>StudioSchema.MAX_BYTES||length>size)throw new IOException("journal_string");
                    byte[] bytes=new byte[length];in.readFully(bytes);
                    value=StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
                }
                if(result.put(key,new StudioTransaction.Slot(present,StudioSchema.value(key,value)))!=null)throw new IOException("journal_duplicate");
            }
            if(in.read()!=-1)throw new IOException("journal_trailing");
        } catch(IllegalArgumentException invalid){throw new IOException("journal_value",invalid);}
        return result;
    }
    public static void write(OutputStream stream,Map<StudioSchema.Key,StudioTransaction.Slot> values)throws IOException {
        if(values.isEmpty()||values.size()>StudioSchema.MAX_KEYS)throw new IOException("journal_count");
        DataOutputStream out=new DataOutputStream(stream);out.writeInt(V2);out.writeInt(values.size());
        for(Map.Entry<StudioSchema.Key,StudioTransaction.Slot> entry:values.entrySet()) {
            StudioSchema.Key key=entry.getKey();Object value=StudioSchema.value(key,entry.getValue().value);
            out.writeUTF(key.section);out.writeUTF(key.id);out.writeBoolean(entry.getValue().present);
            if(value instanceof Boolean)out.writeBoolean((Boolean)value);
            else if(value instanceof Integer)out.writeInt((Integer)value);
            else {
                byte[] bytes=((String)value).getBytes(StandardCharsets.UTF_8);
                if(bytes.length>StudioSchema.MAX_BYTES)throw new IOException("journal_string");
                out.writeInt(bytes.length);out.write(bytes);
            }
        }
        out.flush();
    }
}
