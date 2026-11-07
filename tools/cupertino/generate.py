"""Build an explicit resource map from the checked-in Cupertino glyph catalog.
No fuzzy name lookup or font parsing runs in the Android client.
"""
from pathlib import Path
import json,re,collections,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
RES=ROOT/'TMessagesProj/src/main/res'
CAT=json.loads((Path(__file__).parent/'catalog.json').read_text())
# Ordered semantic families. Brand marks, backgrounds, photos, badges and animation assets stay native.
RULES=[
 ('notify_off notification_off mute unmute silentsound','bell_slash'),('notify notification bell sound','bell'),
 ('unarchive archive','archivebox'),('unpin','pin_slash'),('pin','pin'),('unread readall read checks checkread','checkmark_alt_circle'),
 ('check done select tick','check_mark'),('unblock unlock','lock_open'),('block ban blacklist','hand_raised'),
 ('addcontact contact_add','person_add'),('contact users group members admins people','person_2'),('profile account user person','person'),
 ('newchat message chat discussion discuss comments conversation','chat_bubble'),('channel megaphone broadcast','speaker_2'),
 ('reply','arrowshape_turn_up_left'),('forward','arrowshape_turn_up_right'),('share','square_arrow_up'),
 ('copy duplicate','doc_on_doc'),('paste clipboard','doc_on_clipboard'),('cut','scissors'),
 ('delete trash remove clearcache clear_cache','trash'),('clear close cancel dismiss cross','xmark'),
 ('edit pencil write compose','pencil'),('save gallery photo image picture','photo'),('camera','camera'),
 ('video videocam facetime','video_camera'),('mic voice audio_record','mic'),('headphone','headphones'),
 ('play','play'),('pause','pause'),('stop','stop'),('previous prev','backward_end'),('next','forward_end'),
 ('record','circle_fill'),('volume speaker audio music song media','music_note'),
 ('call_end decline','phone_down'),('call phone','phone'),('download import','arrow_down_to_line'),
 ('upload export','arrow_up_to_line'),('attach clip','paperclip'),('keyboard','keyboard'),
 ('sticker smile emoji folded','smiley'),('gif','rectangle_stack'),('send paperplane','paperplane'),
 ('folder','folder'),('document file docs','doc'),('link url','link'),('unlink','link'),('web browser language globe internet','globe'),
 ('search','search'),('more other options ellipsis','ellipsis'),('menu hamburger','line_horizontal_3'),
 ('settings gear config sliders tools tuning','gear'),('layers stack tabs','square_stack_3d_up'),
 ('gesture hand','hand_draw'),('ghost history recent log timer','clock'),('clock time schedule date calendar','calendar'),
 ('help question','question_circle'),('info about details detail','info'),('privacy passcode secret lock security 2sv key','lock'),
 ('theme palette colorpicker brush appearance','paintbrush'),('dark night moon','moon'),('light sun day brightness','sun_max'),
 ('home house','house'),('cloud sync','cloud'),('reset reload refresh retry restore repeat','arrow_clockwise'),
 ('eye view visibility show','eye'),('hide invisible','eye_slash'),('heart like favorite','heart'),('dislike','hand_thumbsdown'),
 ('thumbsup','hand_thumbsup'),('star premium favorite','star'),('gift birthday','gift'),
 ('bot ai spark magic','sparkles'),('plugin puzzle extension','cube_box'),('wallet payment card pay billing bank','creditcard'),
 ('coin dollar currency cash money','money_dollar_circle'),('battery power','battery_100'),('wifi','wifi'),
 ('data traffic stats chart statistic analytics','chart_bar'),('storage cache database memory','tray_full'),
 ('qr scan','qrcode'),('location map place nearby geo','location'),('compass','compass'),('filter sort','line_horizontal_3_decrease'),
 ('speed','speedometer'),('proxy vpn network connection','shield'),('flash','bolt'),('warning error report alert','exclamationmark_triangle'),
 ('verified shield admin','checkmark_shield'),('flag','flag'),('translate','textformat'),('text font bold italic underline','textformat'),
 ('crop rotate resize aspect','crop'),('brush draw pen','pencil'),('fire hot','flame'),('bug debug','ant'),
 ('back arrow_left leftarrow','chevron_left'),('arrow_right rightarrow chevron_right','chevron_right'),
 ('up arrowup','chevron_up'),('down arrowdown drop_down','chevron_down'),('add plus new','add'),
 ('small','circle'),('expand fullscreen','arrow_up_left_arrow_down_right'),('minimize collapse','arrow_down_right_arrow_up_left'),
 ('reorder list','list_bullet'),('hash hashtag','number'),('logout exit','square_arrow_right'),('login enter','square_arrow_left'),
 ('fast rocket boost boosts','rocket'),('balance scales','scalemass'),('download','arrow_down'),
]
# Specific equivalences override broad families.
EXACT={'ic_ab_back':'chevron_left','ic_ab_other':'ellipsis','input_done':'check_mark','msg_check':'check_mark',
 'msg_settings_old':'gear','msg_photo':'photo','msg_saved':'bookmark','msg_reactions':'smiley','msg_fave':'star',
 'settings3_document':'doc','settings3_sliders':'slider_horizontal_3','settings3_plugins':'cube_box',
 'settings3_hand':'hand_draw','settings3_stack':'square_stack_3d_up','fg_settings_palette':'paintbrush',
 'flexy_composer_voice':'mic','flexy_composer_folded':'smiley','flexy_composer_send':'paperplane',
 'fg_settings_users':'person_2','fg_settings_light':'lightbulb','menu_delete':'trash'}
# Native compact and plural names do not always split into semantic words.
for names,glyph in [
 ('ic_feed ic_feed_filled msg_stories_caption msg_stories_saved msg_stories_views','rectangle_stack'),
 ('ic_player','music_note'),('ic_round_swap_horiz_24','arrow_left_right'),('ic_upward msg_to_beginning','chevron_up'),
 ('input_suggest_paid_24','money_dollar_circle'),('calls_bluetooth','bluetooth'),('calls_headphones','headphones'),
 ('files_empty files_internal msg_sendfile','doc'),('ic_ab_reply2 msg_callback msg_viewreplies','arrowshape_turn_up_left'),
 ('ic_again ic_againinline msg_replace msg_topic_restart','arrow_clockwise'),
 ('ic_gofullscreen ic_goinline msg_maxvideo','arrow_up_left_arrow_down_right'),
 ('ic_outfullscreen ic_outinline msg_minvideo','arrow_down_right_arrow_up_left'),('ic_pauseinline','pause'),('ic_playinline msg_played','play'),
 ('input_bot1 input_bot2 msg_addbot msg_folders_bots','cube_box'),('input_calendar1 input_calendar2 msg_calendar2','calendar'),
 ('msg_actions msg_customize msg_customize_s msg_mini_customize','slider_horizontal_3'),('msg_addbio msg_jobtitle msg_work','briefcase'),
 ('msg_addfolder msg_folders msg_removefolder','folder'),('msg_addphoto msg_photos msg_photoeditor','photo'),
 ('msg_allowspeak msg_voicechat msg_voicechat2 msg_voiceshare','mic'),('msg_calls msg_calls_regular msg_videocall','phone'),
 ('msg_arrow_avatar msg_arrowright msg_inputarrow','arrow_right'),('msg_block2 msg_filled_blocked','hand_raised'),
 ('msg_blur_linear msg_blur_radial','drop'),('msg_blur_off','drop'),('msg_colors','paintbrush'),
 ('msg_contacts msg_contacts_name msg_folders_groups msg_groups msg_ungroup','person_2'),
 ('msg_filled_datausage msg_filled_storageusage','chart_bar'),('msg_filled_general','gear'),
 ('msg_filled_sdcard','tray_full'),('msg_filled_shareout msg_shareout','square_arrow_up'),('msg_filled_stories','rectangle_stack'),
 ('msg_filled_lockedrecord msg_filled_unlockedrecord msg_mini_lock2 msg_mini_lock3 msg_stealth_locked','lock'),
 ('msg_folders_channels msg_screencast','tv'),('msg_screencast_off','tv'),('msg_folders_muted msg_noise_off msg_silent msg_tone_off','bell_slash'),
 ('msg_noise_on msg_notifications msg_tone_on','bell'),('msg_folders_private msg_openprofile','person'),
 ('msg_folders_requests msg_requests','person_add'),('msg_groups_create msg_invited','person_2'),('msg_handdown','hand_raised'),
 ('msg_hybrid msg_satellite','map'),('msg_input_attach2','paperclip'),('msg_instant','bolt'),('msg_leave','square_arrow_right'),
 ('msg_limit_accounts msg_limit_chats msg_limit_groups msg_limit_links msg_limit_stories','exclamationmark_circle'),
 ('msg_link2 msg_openin','link'),('msg_markread msg_seen','check_mark'),('msg_markunread','envelope_badge'),
 ('msg_mention','at'),('msg_mini_addemoji','smiley'),('msg_mini_addstory msg_topic_create','add'),
 ('msg_mini_arrow_mediabold msg_mini_arrow_mediathin msg_mini_replystory msg_mini_replystory2','arrowshape_turn_up_left'),
 ('msg_mini_bomb msg_mini_fireoff msg_mini_fireon','flame'),('msg_mini_closefriends msg_stories_closefriends','person_2'),
 ('msg_mini_forumarrow msg_mini_topicarrow msg_viewintopic msg_topics','number'),
 ('msg_mini_lockedemoji msg_mini_premiumlock','lock'),('msg_mini_stickerstar msg_unfave','star'),
 ('msg_msgbubble msg_msgbubble2 msg_msgbubble3 msg_viewchats','chat_bubble'),('msg_newphone','device_phone_portrait'),
 ('msg_notspam msg_permissions msg_policy','shield'),('msg_online','circle_fill'),('msg_pinnedlist','pin'),
 ('msg_plugins','cube_box'),('msg_pollstop','stop'),('msg_psa','info'),('msg_qrcode','qrcode'),
 ('msg_reactions2 msg_reactions_filled','smiley'),('msg_spoiler msg_stealth_25min msg_stealth_5min msg_stories_stealth msg_stories_stealth2 msg_stories_myhide','eye_slash'),
 ('msg_spoiler_off msg_views','eye'),('msg_stories_order','list_bullet'),('msg_unvote','chart_bar'),('msg_usersearch','person'),
 ('msg_voiceclose','xmark'),('msg_zoomin','zoom_in'),('msg_zoomout','zoom_out'),
]:
 for name in names.split():EXACT[name]=glyph
for names,glyph in [
 ('msg_autodelete msg_mini_autodelete','timer'),('msg_disable','xmark'),('msg_endcall','phone_down'),
 ('msg_filehq','doc'),('msg_filled_general_large','gear'),('msg_devices','device_laptop'),('msg_email','envelope'),
 ('msg_bots','cube_box'),('msg_mask','person_crop_rectangle'),('input_suggest_paid','money_dollar_circle'),
 ('msg_trending','chart_bar'),('msg_status_set','smiley'),('msg_fave','star'),('settings_saved','bookmark'),
 ('settings_chat','chat_bubble'),('settings_data','chart_bar'),('settings_devices','device_laptop'),
 ('settings_help','question_circle'),('settings_language','globe'),('settings_notifications','bell'),
 ('settings_privacy','lock'),('settings_appearance','paintbrush'),('plugins_filled','cube_box'),
 ('filled_profile_settings','gear'),('filled_profile_call','phone'),
]:
 for name in names.split():EXACT[name]=glyph
for names,glyph in [
 ('baseline_adjust_24','circle_lefthalf_fill'),('baseline_alternate_email_12 baseline_alternate_email_24 filled_username','at'),
 ('baseline_arrow_downward_24','arrow_down'),('baseline_arrow_upward_18 baseline_arrow_upward_24','arrow_up'),
 ('baseline_assignment_24','doc_on_clipboard'),('baseline_backspace_24','delete_left'),('baseline_bluetooth_24 filled_calls_bluetooth_s','bluetooth'),
 ('baseline_bookmark_24 chats_saved outline_saved_24 msg_saved_filled','bookmark'),('baseline_build_24 outline_craft filled_forge','hammer'),
 ('baseline_bullhorn_16 baseline_bullhorn_24 baseline_bullhorn_56','speaker_2'),
 ('baseline_code_24 baseline_developer_mode_24 formatting_code','chevron_left_slash_chevron_right'),
 ('baseline_collections_16','rectangle_stack'),('baseline_create_24','pencil'),
 ('baseline_directions_24 filled_directions','location'),('baseline_directions_car_24','car'),
 ('baseline_emoticon_24 baseline_emoticon_outline_24 smiles_tab_smiles','smiley'),('baseline_explore_24','compass'),
 ('baseline_format_color_fill_24','paintbrush'),('baseline_format_underlined_24','underline'),
 ('baseline_forum_24 baseline_forum_96','chat_bubble_2'),('baseline_gps_fixed_12 baseline_gps_fixed_16 baseline_gps_fixed_24','location'),
 ('baseline_mail_96','envelope'),('baseline_notifications_24 outline_notifications_24 notifications_on','bell'),
 ('baseline_notifications_off_24 baseline_notifications_paused_24 notifications_off','bell_slash'),
 ('baseline_opacity_18','drop'),('baseline_party_popper_16','burst'),('baseline_poll_16 baseline_poll_24','chart_bar'),
 ('baseline_public_24','globe'),('baseline_receipt_16','doc_text'),('baseline_redo_18','arrow_uturn_right'),
 ('baseline_replay_24 outline_revert_24 chats_undo','arrow_counterclockwise'),('baseline_signal_cellular_alt_24','antenna_radiowaves_left_right'),
 ('baseline_stars_18 baseline_stars_24 filled_earn_stars filled_giveaway_stars','star'),
 ('baseline_strikethrough_s_24 formatting_strikethrough','strikethrough'),('baseline_swap_horiz_24','arrow_left_right'),
 ('baseline_system_update_24','arrow_down_square'),('baseline_toc_24','list_bullet'),('baseline_tune_24','slider_horizontal_3'),
 ('baseline_undo_18 baseline_undo_24','arrow_uturn_left'),('baseline_unsubscribe_24','envelope_badge'),
 ('baseline_videogame_asset_16','gamecontroller'),('baseline_watch_later_24','clock'),('baseline_whatshot_24 outline_whatshot_24','flame'),
 ('chats_replies','arrowshape_turn_up_left'),('filled_chatlist2 outline_fab_story_24','chat_bubble'),
 ('filled_chatlist_mention','at'),('filled_chatlist_poll','chart_bar'),('filled_chatlist_reaction filled_reactions','smiley'),
 ('filled_gram_earnings filled_messages_paid filled_paid_suggest_24','money_dollar_circle'),
 ('filled_poll_deadline_24','timer'),('filled_poll_multiple_24','square_list'),('filled_poll_revote_24','arrow_clockwise'),
 ('filled_poll_shuffle_24','shuffle'),('filled_requests_24','person_add'),('filled_sharing_off2_24','xmark'),
 ('filled_understood','check_mark'),('filled_verify_age','person_crop_circle_badge_checkmark'),
 ('formatting_marked','list_bullet'),('formatting_math','function'),('formatting_quote','quote_bubble'),('formatting_spoiler','eye_slash'),
 ('msg_qrcode_mini','qrcode'),('outline_caption_24 outline_caption','captions_bubble'),('outline_groups_24','person_2'),
 ('permissions_camera1 permissions_camera2','camera'),('permissions_gallery1 permissions_gallery2','photo'),
 ('smiles_inputsearch','search'),('filled_access_sleeping','moon_zzz'),('filled_affiliate','link'),('filled_chatlink_large','link'),
 ('filled_sensitive','eye_slash'),('filled_unclaimed','gift'),('filled_unknown','question_circle'),('filled_views','eye'),('smiles_tab_stickers','smiley'),
]:
 for name in names.split():EXACT[name]=glyph
for names,glyph in [
 ('baseline_sports_baseball_24 outline_sports_baseball_24','flexy_baseball'),
 ('baseline_fingerprint_24 filled_access_fingerprint','flexy_fingerprint'),
 ('filled_crown_on filled_rating_crown filled_stream_crown filled_stream_crown_outline','flexy_crown'),
 ('filled_crown_off','flexy_crown_off'),('filled_poll_correct_24','check_mark_circled'),
]:
 for name in names.split():EXACT[name]=glyph
PREFIXES=('baseline_','msg_','menu_','ic_','input_','profile_','settings3_','fg_settings_','flexy_composer_','header_','chat_','player_','sheet_','group_','files_','search_','action_','calls_','settings_','filled_','outline_','tabs_','media_','photo_','attach_','call_','plugins_','smiles_','list_','chats_','dialog_','formatting_','notifications_','permissions_')
EXCLUDE=re.compile(r'(?:\.9|_bg(?:_|$)|background|shadow|gradient|selector|popup|border|divider|scrim|wallpaper|(?:^|_)logo(?:_|$)|level\d|photo_placeholder|notification(?:_\w+)?$)')
files={}
for p in sorted(RES.glob('drawable*/*')):
 if p.suffix in ('.xml','.png','.webp') and not EXCLUDE.search(p.stem) and p.stem.startswith(PREFIXES):
  if p.stem not in files or p.parent.name=='drawable':files[p.stem]=p
mapped={};skipped={};missing_glyphs=set();ns='{http://schemas.android.com/apk/res/android}'
for name,p in files.items():
 width=height=24
 color=0xff000000
 mirrored=False
 if any(x in name for x in ('halfcheck','autodelete_','autodelete_badge','min_autodelete','launcher','masks_msk','lockedrecord','unlockedrecord')):skipped[name]='native layered state or branded graphic';continue
 if p.suffix=='.xml':
  try:root=ET.parse(p).getroot()
  except ET.ParseError:continue
  if root.tag!='vector':skipped[name]='stateful or non-vector resource';continue
  mirrored=root.get(ns+'autoMirrored')=='true'
  colors=set()
  for node in root.iter():
   raw=node.get(ns+'fillColor') or node.get(ns+'strokeColor')
   if raw and raw.startswith('#'):
    digits=raw[1:]
    if len(digits)==6:digits='ff'+digits
    if len(digits)==8 and int(digits[:2],16)>0:colors.add(int(digits,16))
  if len(colors)>1:skipped[name]='native multicolor composition';continue
  if colors:color=next(iter(colors))
  for attr,default in [('width',24),('height',24)]:
   raw=root.get(ns+attr,'24dp');m=re.fullmatch(r'([\d.]+)(?:dp|dip)',raw)
   v=round(float(m[1])) if m else default
   if attr=='width':width=v
   else:height=v
 elif p.suffix in ('.png','.webp'):
  from PIL import Image
  with Image.open(p) as im:
   density=next((d for d in ['xxxhdpi','xxhdpi','xhdpi','hdpi','mdpi'] if d in p.parent.name),'mdpi')
   scale={'xxxhdpi':4,'xxhdpi':3,'xhdpi':2,'hdpi':1.5,'mdpi':1}[density];width=round(im.width/scale);height=round(im.height/scale)
 if name in ('baseline_android_24','ic_gram','outline_gram_24'):
  skipped[name]='platform or application brand';continue
 if 'mute1h' in name or 'mute2d' in name or name=='msg_round_load_m':
  skipped[name]='native duration or progress indicator';continue
 if not 4<=width<=96 or not 4<=height<=96:skipped[name]='illustration or large graphic';continue
 base_name=re.sub(r'_(?:solar|remix)(?:_\d+)?$','',name)
 base_name=re.sub(r'_(?:14|hw|ny)$','',base_name)
 glyph=EXACT.get(base_name)
 if glyph is None:
  tokens=base_name.split('_');joined='_'.join(tokens[1:])
  for words,candidate in RULES:
   if any(w in tokens or w==joined or ('_' in w and w in joined) for w in words.split()):glyph=candidate;break
 if glyph is None:skipped[name]='needs semantic review';continue
 if glyph not in CAT:missing_glyphs.add(glyph);continue
 mapped[name]={'glyph':glyph,'codepoint':CAT[glyph],'width':width,'height':height,'color':color,'mirrored':mirrored}
if missing_glyphs:raise SystemExit('Unknown Cupertino glyphs: '+', '.join(sorted(missing_glyphs)))
source='''// Generated by tools/cupertino/generate.py. Supports non-final Android resource IDs.
package app.flexygram.icons;
import org.telegram.messenger.R;
public final class CupertinoIconMap {
 private CupertinoIconMap() {}
 private static final class Holder {
  static final long[] SPECS=buildSpecs(), COLORS=buildColors();
 }
 public static int spec(int id){return id<=0?0:lookup(Holder.SPECS,id,0);}
 public static int color(int id){return lookup(Holder.COLORS,id,0xff000000);}
 private static int lookup(long[] data,int id,int fallback){
  int low=0,high=data.length-1;
  while(low<=high){int mid=(low+high)>>>1,key=(int)(data[mid]>>>32);
   if(key<id)low=mid+1;else if(key>id)high=mid-1;else return (int)data[mid];}
  return fallback;
 }
 private static long[] buildSpecs(){
  long[] data={
'''
for name,spec in sorted(mapped.items()):
 packed=spec['codepoint'] | spec['width']<<16 | spec['height']<<24 | (0x80000000 if spec['mirrored'] else 0)
 source+=f'   ((long) R.drawable.{name} << 32) | 0x{packed:08x}L, // {spec["glyph"]}\n'
source+='  };\n  java.util.Arrays.sort(data);return data;\n }\n private static long[] buildColors(){\n  long[] data={\n'
for name,spec in sorted(mapped.items()):
 if spec['color']!=0xff000000:source+=f'   ((long) R.drawable.{name} << 32) | 0x{spec["color"]:08x}L,\n'
source+='  };\n  java.util.Arrays.sort(data);return data;\n }\n}\n'
(ROOT/'TMessagesProj/src/main/java/app/flexygram/icons/CupertinoIconMap.java').write_text(source)
(Path(__file__).parent/'mapping.json').write_text(json.dumps(mapped,indent=2)+'\n')
(Path(__file__).parent/'unmapped.json').write_text(json.dumps(skipped,indent=2)+'\n')
print(f'Mapped {len(mapped)} static icon resources; {len(skipped)} retained for review/state/geometry.')
