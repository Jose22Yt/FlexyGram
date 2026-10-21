package io.github.jose22yt.flexygram.login;

import java.nio.ByteBuffer;
import java.nio.CharBuffer;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import org.telegram.messenger.SRPHelper;
import org.telegram.tgnet.TLRPC;
import org.telegram.tgnet.tl.TL_account;
import io.github.jose22yt.flexygram.session.RequestCoordinator.Domain;

/** Original SRPHelper only. Invoke on serial worker with synthetic data; opens no transport. */
public final class OriginalSrpLocalProof implements TelegramRequestContext.LocalProof {
    @Override public Domain domain(){return Domain.LOCAL_SIMULATION;}
    @Override public TLRPC.TL_inputCheckPasswordSRP create(char[] synthetic,TL_account.Password parameters) {
        if(synthetic==null||synthetic.length==0||parameters==null||!parameters.has_password
                ||!(parameters.current_algo instanceof TLRPC.TL_passwordKdfAlgoSHA256SHA256PBKDF2HMACSHA512iter100000SHA256ModPow))
            throw new IllegalArgumentException("LOCAL_SRP_PARAMETERS_REQUIRED");
        ByteBuffer encoded=StandardCharsets.UTF_8.encode(CharBuffer.wrap(synthetic));
        byte[] password=new byte[encoded.remaining()],x=null;
        try {
            encoded.get(password);
            TLRPC.TL_passwordKdfAlgoSHA256SHA256PBKDF2HMACSHA512iter100000SHA256ModPow algo=(TLRPC.TL_passwordKdfAlgoSHA256SHA256PBKDF2HMACSHA512iter100000SHA256ModPow)parameters.current_algo;
            x=SRPHelper.getX(password,algo);
            return SRPHelper.startCheck(x,parameters.srp_id,parameters.srp_B,algo);
        }catch(RuntimeException|LinkageError unavailable){throw new IllegalStateException("LOCAL_SRP_UNAVAILABLE");}
        finally{Arrays.fill(password,(byte)0);if(x!=null)Arrays.fill(x,(byte)0);if(encoded.hasArray())Arrays.fill(encoded.array(),(byte)0);}
    }
}
