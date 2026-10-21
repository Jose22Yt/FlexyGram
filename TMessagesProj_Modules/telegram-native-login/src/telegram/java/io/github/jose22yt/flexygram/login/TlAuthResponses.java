package io.github.jose22yt.flexygram.login;

import org.telegram.tgnet.TLObject;
import org.telegram.tgnet.TLRPC;
import org.telegram.tgnet.tl.TL_account;
import io.github.jose22yt.flexygram.login.NativeLoginProtocol.*;
import io.github.jose22yt.flexygram.login.NativeLoginProtocol.Error;

/** Typed boundary for original TL classes. Retains no response/error or private values. */
public final class TlAuthResponses {
    private TlAuthResponses() {}
    public static Response map(Action action,TLObject response,TLRPC.TL_error error) {
        if(action==null || response!=null&&error!=null)return Response.failure(Error.PROTOCOL);
        if(error!=null)return NativeLoginProtocol.error(error.text);
        if(response==null)return Response.failure(Error.PROTOCOL);
        if(action==Action.SEND_CODE) {
            if(response instanceof TLRPC.TL_auth_sentCodeSuccess)return authorization(((TLRPC.TL_auth_sentCodeSuccess)response).authorization);
            if(response instanceof TLRPC.TL_auth_sentCodePaymentRequired)return Response.code(Route.PAYMENT);
            if(response instanceof TLRPC.TL_auth_sentCode) {
                TLRPC.TL_auth_sentCode code=(TLRPC.TL_auth_sentCode)response;
                if(code.phone_code_hash==null||code.phone_code_hash.isEmpty())return Response.failure(Error.PROTOCOL);
                Route route=route(code.type);return route==Route.NONE?Response.of(Kind.UNSUPPORTED):Response.code(route);
            }
        } else if(action==Action.GET_PASSWORD && response instanceof TL_account.Password) {
            TL_account.Password password=(TL_account.Password)response;
            return password.has_password && password.current_algo instanceof TLRPC.TL_passwordKdfAlgoSHA256SHA256PBKDF2HMACSHA512iter100000SHA256ModPow
                    && password.srp_id!=0 && password.srp_B!=null && password.srp_B.length>0
                    ?Response.of(Kind.PASSWORD_PARAMETERS):Response.of(Kind.UNSUPPORTED);
        } else if(action==Action.EXPORT_QR || action==Action.IMPORT_QR) {
            if(response instanceof TLRPC.TL_auth_loginTokenSuccess)return authorization(((TLRPC.TL_auth_loginTokenSuccess)response).authorization);
            if(response instanceof TLRPC.TL_auth_loginTokenMigrateTo) {
                TLRPC.TL_auth_loginTokenMigrateTo token=(TLRPC.TL_auth_loginTokenMigrateTo)response;
                if(token.token==null||token.token.length==0)return Response.failure(Error.PROTOCOL);
                return Response.migration(token.dc_id);
            }
            if(response instanceof TLRPC.TL_auth_loginToken) {
                TLRPC.TL_auth_loginToken token=(TLRPC.TL_auth_loginToken)response;
                return token.token!=null&&token.token.length>0&&token.expires>0?Response.of(Kind.QR_TOKEN):Response.failure(Error.PROTOCOL);
            }
        } else if(action==Action.SIGN_IN || action==Action.CHECK_PASSWORD || action==Action.SIGN_UP) {
            return authorization(response);
        }
        return Response.failure(Error.PROTOCOL);
    }
    private static Response authorization(TLObject value) {
        if(value instanceof TLRPC.TL_auth_authorizationSignUpRequired)
            return Response.signup(((TLRPC.TL_auth_authorizationSignUpRequired)value).terms_of_service!=null);
        if(value instanceof TLRPC.TL_auth_authorization) {
            TLRPC.TL_auth_authorization auth=(TLRPC.TL_auth_authorization)value;
            return auth.user!=null && !auth.setup_password_required?Response.of(Kind.AUTHORIZED):Response.of(Kind.UNSUPPORTED);
        }
        return Response.failure(Error.PROTOCOL);
    }
    private static Route route(TLRPC.auth_SentCodeType type) {
        if(type instanceof TLRPC.TL_auth_sentCodeTypeApp)return Route.APP;
        if(type instanceof TLRPC.TL_auth_sentCodeTypeSms)return Route.SMS;
        if(type instanceof TLRPC.TL_auth_sentCodeTypeCall)return Route.CALL;
        if(type instanceof TLRPC.TL_auth_sentCodeTypeFlashCall)return Route.FLASH_CALL;
        if(type instanceof TLRPC.TL_auth_sentCodeTypeMissedCall)return Route.MISSED_CALL;
        if(type instanceof TLRPC.TL_auth_sentCodeTypeSmsWord)return Route.WORD;
        if(type instanceof TLRPC.TL_auth_sentCodeTypeSmsPhrase)return Route.PHRASE;
        if(type instanceof TLRPC.TL_auth_sentCodeTypeFragmentSms)return Route.FRAGMENT_SMS;
        if(type instanceof TLRPC.TL_auth_sentCodeTypeEmailCode)return Route.EMAIL;
        if(type instanceof TLRPC.TL_auth_sentCodeTypeSetUpEmailRequired)return Route.SETUP_EMAIL;
        if(type instanceof TLRPC.TL_auth_sentCodeTypeFirebaseSms)return Route.FIREBASE;
        return Route.NONE;
    }
}
