package io.github.jose22yt.flexygram.login;

import io.github.jose22yt.flexygram.login.NativeLoginProtocol.*;

/** Read-only native page routing. A page number is NOT permission to execute its lifecycle. */
public final class NativePagePlan {
    public enum Page {
        KEEP(-1),PHONE(0),APP_CODE(1),SMS_CODE(2),FLASH_CALL(3),CALL(4),REGISTER(5),PASSWORD(6),MISSED_CALL(11),WORD(16),PHRASE(17),QR(19);
        public final int originalViewNumber;Page(int value){originalViewNumber=value;}
    }
    public enum Block { NONE, ORIGINAL_PARAMETERS_REQUIRED, ORIGINAL_OBSERVERS_REVIEW, QR_LIFECYCLE_REVIEW, UNSUPPORTED }
    public final Page page;public final Block block;public final Stage stage;public final NativeLoginProtocol.Error error;
    private NativePagePlan(Page page,Block block,NativeLoginTransport.Snapshot state){this.page=page;this.block=block;stage=state.stage;error=state.error;}
    public boolean mayEnterOriginalPage(){return block==Block.NONE;}
    public static NativePagePlan from(NativeLoginTransport.Snapshot state) {
        if(state==null)throw new IllegalArgumentException("NATIVE_STATE_REQUIRED");
        Page page=Page.KEEP;Block block=Block.NONE;
        switch(state.stage) {
        case NEW:case READY:page=Page.PHONE;break;
        case CODE_REQUIRED:case CODE_RETRY:
            switch(state.route){
            case APP:page=Page.APP_CODE;break;case SMS:page=Page.SMS_CODE;break;
            case CALL:page=Page.CALL;break;case FLASH_CALL:page=Page.FLASH_CALL;break;
            case MISSED_CALL:page=Page.MISSED_CALL;break;case WORD:page=Page.WORD;break;
            case PHRASE:page=Page.PHRASE;break;default:block=Block.UNSUPPORTED;
            }
            if(block==Block.NONE)block=(page==Page.SMS_CODE||page==Page.FLASH_CALL)?Block.ORIGINAL_OBSERVERS_REVIEW:Block.ORIGINAL_PARAMETERS_REQUIRED;
            break;
        case PASSWORD_REQUIRED:case PASSWORD_PARAMETERS:page=Page.PASSWORD;block=Block.ORIGINAL_PARAMETERS_REQUIRED;break;
        case SIGNUP_REQUIRED:page=Page.REGISTER;block=Block.ORIGINAL_PARAMETERS_REQUIRED;break;
        case QR_TOKEN:case QR_MIGRATION:page=Page.QR;block=Block.QR_LIFECYCLE_REVIEW;break;
        case FAILED:case CLOSED:block=Block.UNSUPPORTED;break;
        default:break; // busy/wait/authorization keeps current native page; never calls onAuthSuccess.
        }
        return new NativePagePlan(page,block,state);
    }
}
