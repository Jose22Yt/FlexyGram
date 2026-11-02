/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.memberlens;

import android.content.Context;
import android.os.Bundle;
import android.os.Parcelable;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import java.lang.ref.WeakReference;
import java.util.ArrayList;
import org.telegram.messenger.*;
import org.telegram.tgnet.TLRPC;
import org.telegram.ui.ActionBar.*;
import org.telegram.ui.ChatActivity;
import org.telegram.ui.FilteredSearchView;
import org.telegram.ui.Components.*;

/** Temporary native search surface. The underlying ChatActivity and its layout remain untouched. */
public final class MemberLensActivity extends BaseFragment {
    private final WeakReference<ChatActivity> origin;
    private MemberLensScope scope;
    private FilteredSearchView results;
    private EditTextBoldCursor queryField;
    private TextView state, name, subtitle;
    private ProgressBar progress;
    private LinearLayout root, capsule;
    private ImageView close, search;
    private Parcelable scrollState;
    private String query="";
    public MemberLensActivity(Bundle args){this(args,null);}
    public MemberLensActivity(Bundle args,ChatActivity origin){super(args);this.origin=new WeakReference<>(origin);}
    @Override public boolean onFragmentCreate(){
        try{scope=new MemberLensScope(currentAccount,arguments.getLong("lens_dialog"),arguments.getLong("lens_user"),arguments.getInt("lens_topic"));}
        catch(IllegalArgumentException invalid){return false;}
        TLRPC.Chat group=getMessagesController().getChat(-scope.dialogId);
        if(group==null || ChatObject.isChannelAndNotMegaGroup(group) || ChatObject.isMonoForum(group))return false;
        query=arguments.getString("lens_query","");
        return super.onFragmentCreate();
    }
    @Override public View createView(Context context){
        FilteredSearchView.MemberLensSnapshot saved=null;
        if(results!=null){scrollState=results.layoutManager.onSaveInstanceState();saved=results.saveMemberLensState();results.disposeMemberLens();}
        actionBar.setBackButtonImage(R.drawable.ic_ab_back);
        actionBar.setTitle(LocaleController.getString(R.string.MemberLensSubtitle));
        actionBar.setActionBarMenuOnItemClick(new ActionBar.ActionBarMenuOnItemClick(){@Override public void onItemClick(int id){if(id==-1)finishFragment();}});
        root=new LinearLayout(context);root.setOrientation(LinearLayout.VERTICAL);
        fragmentView=root;
        capsule=new LinearLayout(context);capsule.setGravity(Gravity.CENTER_VERTICAL);capsule.setPadding(AndroidUtilities.dp(8),AndroidUtilities.dp(6),AndroidUtilities.dp(4),AndroidUtilities.dp(6));
        TLRPC.User user=getMessagesController().getUser(scope.userId);
        BackupImageView avatar=new BackupImageView(context);avatar.setRoundRadius(AndroidUtilities.dp(20));
        AvatarDrawable placeholder=new AvatarDrawable();if(user!=null)placeholder.setInfo(user);
        avatar.setImage(ImageLocation.getForUser(user,ImageLocation.TYPE_SMALL),"50_50",placeholder,user);
        capsule.addView(avatar,LayoutHelper.createLinear(40,40));
        LinearLayout labels=new LinearLayout(context);labels.setOrientation(LinearLayout.VERTICAL);labels.setPaddingRelative(AndroidUtilities.dp(10),0,0,0);
        name=new TextView(context);name.setText(user==null?Long.toString(scope.userId):UserObject.getUserName(user));name.setTextSize(16);name.setSingleLine(true);name.setEllipsize(android.text.TextUtils.TruncateAt.END);
        subtitle=new TextView(context);subtitle.setText(LocaleController.getString(R.string.MemberLensSubtitle));subtitle.setTextSize(12);
        labels.addView(name);labels.addView(subtitle);capsule.addView(labels,new LinearLayout.LayoutParams(0,-2,1));
        search=new ImageView(context);search.setImageResource(R.drawable.msg_search);search.setContentDescription(LocaleController.getString(R.string.Search));
        close=new ImageView(context);close.setImageResource(R.drawable.msg_close);close.setContentDescription(LocaleController.getString(R.string.Close));
        capsule.addView(search,LayoutHelper.createLinear(48,48));capsule.addView(close,LayoutHelper.createLinear(48,48));
        root.addView(capsule,LayoutHelper.createLinear(-1,-2));
        queryField=new EditTextBoldCursor(context);queryField.setTextSize(16);queryField.setSingleLine(true);queryField.setHint(LocaleController.getString(R.string.Search));queryField.setPadding(AndroidUtilities.dp(16),0,AndroidUtilities.dp(16),0);
        queryField.setText(query);queryField.setVisibility(query.isEmpty()?View.GONE:View.VISIBLE);root.addView(queryField,LayoutHelper.createLinear(-1,48));
        progress=new ProgressBar(context,null,android.R.attr.progressBarStyleHorizontal);progress.setIndeterminate(true);root.addView(progress,LayoutHelper.createLinear(-1,2));
        state=new TextView(context);state.setTextSize(13);state.setPadding(AndroidUtilities.dp(16),AndroidUtilities.dp(8),AndroidUtilities.dp(16),AndroidUtilities.dp(8));root.addView(state,LayoutHelper.createLinear(-1,-2));
        results=new FilteredSearchView(this);
        results.configureMemberLens(scope,this::goToOriginal,this::updateState);
        root.addView(results,new LinearLayout.LayoutParams(-1,0,1));
        queryField.addTextChangedListener(new TextWatcher(){public void beforeTextChanged(CharSequence s,int start,int count,int after){}public void onTextChanged(CharSequence s,int start,int before,int count){query=s.toString();arguments.putString("lens_query",query);scrollState=null;runSearch();}public void afterTextChanged(Editable e){}});
        search.setOnClickListener(v->{queryField.setVisibility(View.VISIBLE);queryField.requestFocus();AndroidUtilities.showKeyboard(queryField);});
        close.setOnClickListener(v->finishFragment());state.setOnClickListener(v->{if(results!=null)results.retryMemberLens();});
        applyColors();if(!results.restoreMemberLensState(saved,query))runSearch();return fragmentView;
    }
    private void runSearch(){if(results!=null)results.search(scope.dialogId,0,0,0,null,false,query,true);}
    private void updateState(){
        if(results==null||state==null)return;
        progress.setVisibility(results.memberLensLoading()?View.VISIBLE:View.GONE);
        boolean failed=results.memberLensFailed();state.setText(LocaleController.getString(failed?R.string.MemberLensError:R.string.MemberLensEmpty));
        state.setVisibility(failed||!results.memberLensLoading()&&results.messages.isEmpty()?View.VISIBLE:View.GONE);
        state.setClickable(failed);
        if(scrollState!=null&&!results.messages.isEmpty()){results.layoutManager.onRestoreInstanceState(scrollState);scrollState=null;}
    }
    private void goToOriginal(MessageObject message){
        if(message==null||!scope.accepts(message.getDialogId(),message.getFromChatId()))return;
        AndroidUtilities.hideKeyboard(queryField);
        ChatActivity chat=origin.get();
        if(chat!=null&&chat.openMemberLensOriginal(message.getId())){
            finishFragment();
        }else{
            Bundle args=new Bundle();args.putLong("chat_id",-scope.dialogId);args.putInt("message_id",message.getId());
            ChatActivity target=new ChatActivity(args);target.setCurrentAccount(scope.account);
            if(scope.topicId!=0){
                TLRPC.TL_forumTopic topic=getMessagesController().getTopicsController().findTopic(-scope.dialogId,scope.topicId);
                if(topic==null||topic.topicStartMessage==null){AlertsCreator.showSimpleAlert(this,LocaleController.getString(R.string.ErrorOccurred));return;}
                ArrayList<MessageObject> starter=new ArrayList<>();starter.add(new MessageObject(scope.account,topic.topicStartMessage,false,false));
                target.setThreadMessages(starter,getMessagesController().getChat(-scope.dialogId),topic.id,topic.read_inbox_max_id,topic.read_outbox_max_id,topic);
            }
            presentFragment(target,true);
        }
    }
    private void applyColors(){
        if(root==null)return;
        int text=getThemedColor(Theme.key_windowBackgroundWhiteBlackText),secondary=getThemedColor(Theme.key_windowBackgroundWhiteGrayText);
        root.setBackgroundColor(getThemedColor(Theme.key_windowBackgroundGray));capsule.setBackground(Theme.createRoundRectDrawable(AndroidUtilities.dp(16),getThemedColor(Theme.key_windowBackgroundWhite)));
        name.setTextColor(text);subtitle.setTextColor(secondary);state.setTextColor(secondary);queryField.setTextColor(text);queryField.setHintTextColor(secondary);
        search.setColorFilter(text);close.setColorFilter(text);
        if(results!=null)results.recyclerListView.invalidateViews();
    }
    @Override public Theme.ResourcesProvider getResourceProvider(){ChatActivity chat=origin==null?null:origin.get();return chat==null?super.getResourceProvider():chat.getResourceProvider();}
    @Override public ArrayList<ThemeDescription> getThemeDescriptions(){
        ArrayList<ThemeDescription> descriptions=super.getThemeDescriptions();
        if(results!=null)descriptions.addAll(results.getThemeDescriptions());
        descriptions.add(new ThemeDescription(null,0,null,null,null,this::applyColors,Theme.key_windowBackgroundWhiteBlackText));
        return descriptions;
    }
    @Override public void onResume(){super.onResume();if(scope!=null&&UserConfig.selectedAccount!=scope.account)finishFragment();}
    @Override public void onPause(){if(results!=null)scrollState=results.layoutManager.onSaveInstanceState();super.onPause();}
    @Override public void onFragmentDestroy(){if(queryField!=null)AndroidUtilities.hideKeyboard(queryField);if(results!=null)results.disposeMemberLens();results=null;super.onFragmentDestroy();}
}
