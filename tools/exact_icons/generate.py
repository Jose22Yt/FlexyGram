#!/usr/bin/env python3
"""Generate a reviewed semantic default map; never infer icons from a broad substring.

PNG bytes come unchanged from the user's v2 archive (assets.json records provenance).
Unrepresented actions/states retain their distinct native resource, including checks,
repeat-one, keyboard, previous/next, unpin, call-end and disabled controls.
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
RES = ROOT / 'TMessagesProj/src/main/res'
# Exact base names; pack variants share the action only when Default is selected.
GROUPS = {
 'enviar': 'msg_send attach_send input_send flexy_composer_send',
 'inicio': 'msg_home baseline_home_24',
 'mensaje_tres_puntos': 'msg_message msg_discussion msg_discuss settings_chat settings3_chat fg_settings_chat fg_settings_chats menu_chats outline_profile_message_24 filled_profile_message_24 profile_newmsg profile_newmsg_filled',
 'chats_dobles': 'tabs_chats_24 tabs_chats_active_24 tabs_chats tabs_chats_active baseline_forum_24 baseline_forum_96',
 'llamar': 'msg_calls msg_call msg_callback chat_calls_voice profile_phone outline_profile_call_24 filled_profile_call_24 tabs_calls_24 tabs_calls_active_24 tabs_calls_active tabs_calls menu_calls settings_calls baseline_call_24',
 'videollamada': 'profile_video chat_calls_video calls_video input_video input_video_pressed flexy_composer_video outline_profile_video_24 filled_profile_video_24 menu_videocall',
 'perfil': 'msg_openprofile tabs_contacts_24 tabs_contact_active_24 tabs_contacts_active settings_account baseline_person_16 baseline_person_24 baseline_person_56',
 'contactos': 'msg_contacts msg_contact menu_contacts tabs_contacts baseline_contact_phone_24',
 'grupos': 'msg_groups msg_folders_groups settings_group baseline_group_16 baseline_group_24 baseline_group_56 baseline_group_96',
 'grupo_nuevo': 'msg_newgroup baseline_group_add_24',
 'agregar_contacto': 'msg_addcontact msg_contact_add baseline_person_add_24 outline_add_account',
 'buscar': 'msg_search msg_search_14 msg_search_24 ic_ab_search outline_header_search outline_search_1_24 smiles_inputsearch msg_user_search msg_usersearch',
 'notificaciones': 'msg_notifications msg_unmute settings_sounds',
 'notificaciones_silenciadas': 'msg_mute',
 'calendario': 'msg_calendar menu_date baseline_date_range_10 baseline_date_range_24',
 'reloj': 'msg_recent menu_recent msg_history settings3_ghost fg_settings_history baseline_access_time_24 baseline_access_time_filled_24',
 'guardados': 'msg_saved chats_saved menu_saved',
 'favoritos': 'msg_fave msg_faves emoji_tabs_faves settings_stars',
 'corazon': 'msg_reactions msg_reactions_filled baseline_favorite_20',
 'fijar': 'msg_pin chats_pin',
 'ajustes': 'msg_settings msg_settings_old menu_settings settings3_sliders fg_settings_settings smiles_tab_settings outline_profile_settings filled_profile_settings',
 'controles': 'fg_settings_gesture fg_settings_estilo_de_interfaz settings3_hand msg_gesture msg_hand',
 'apariencia': 'msg_theme filter_palette fg_settings_palette fg_settings_home fg_settings_apariencia',
 'pincel': 'photo_paint_brush baseline_brush_24',
 'imagen': 'msg_photos msg_gallery files_gallery baseline_image_24 baseline_image_96 baseline_image_aspect_ratio_24 permissions_gallery1 permissions_gallery2',
 'camara': 'camera msg_camera fg_settings_camera baseline_camera_alt_16 baseline_camera_alt_24 baseline_camera_alt_96',
 'video': 'msg_videos',
 'musica': 'msg_music msg_audio msg_folders_music baseline_music_note_24',
 'documento': 'msg_document msg_view_file settings3_document fg_settings_file bot_file baseline_insert_drive_file_16 baseline_insert_drive_file_24 baseline_insert_drive_file_96',
 'archivo_comprimido': 'msg_zip',
 'estadisticas': 'msg_stats msg_statistics baseline_data_usage_24 baseline_bubble_chart_24',
 'grafico': 'msg_chart',
 'carpeta': 'msg_folder files_folder settings_folders settings3_folder fg_settings_folder',
 'descargar': 'msg_download fg_settings_download fg_settings_otros baseline_file_download_24 baseline_cloud_download_24',
 'subir': 'msg_upload',
 'nube_sincronizar': 'cloud_sync fg_settings_cloud',
 'agenda_contactos': 'msg_contact_phone',
 'contacto_nuevo': 'msg_contact_new',
 'grupo': 'msg_addgroup',
 'anuncios': 'msg_channel settings_channel fg_settings_canales',
 'transmision': 'msg_live',
 'altavoz': 'msg_broadcast',
 'bot': 'input_bot1 input_bot2 msg_addbot msg_folders_bots',
 'bot_ia': 'ai_chat',
 'destellos_ia': 'msg_ai',
 'panel': 'fg_settings_general msg_media',
 'capas': 'msg_layers msg_tabs settings3_stack fg_settings_layers fg_settings_iconos',
 'proteccion': 'settings_privacy outline_shield_check outline_shield_plain_24',
 'candado': 'msg_secret msg_lock menu_secret baseline_lock_14 baseline_lock_24 baseline_lock_48',
 'clave': 'msg_password',
 'huella': 'baseline_fingerprint_24',
 'escanear': 'qr_scan',
 'codigo_qr': 'msg_qrcode msg_qr profile_qr_scan_24 outline_header_qr_24',
 'enlace': 'msg_link filled_link baseline_link_24',
 'desenlazar': 'msg_unlink',
 'etiqueta': 'msg_tag menu_tag_filter',
 'eliminar': 'msg_delete msg_clearcache fg_settings_trash baseline_delete_18 baseline_delete_24 baseline_delete_forever_24 baseline_delete_sweep_24',
 'lapiz': 'msg_edit baseline_edit_12 baseline_edit_24 baseline_create_24',
 'editar': 'msg_edit_name',
 'retroceder': 'ic_ab_back flexy_ios_back baseline_arrow_back_24 baseline_keyboard_arrow_left_24',
 'avanzar': 'msg_arrowright baseline_arrow_forward_24',
 'arriba': 'msg_go_up baseline_keyboard_arrow_up_24',
 'abajo': 'msg_go_down arrow_more baseline_keyboard_arrow_down_20 baseline_keyboard_arrow_down_24 baseline_direction_arrow_down_24',
 'tres_puntos_vertical': 'msg_more',
 'tres_puntos_horizontal': 'ic_ab_other',
 'filtro': 'msg_filter',
 'ordenar': 'msg_sort menu_sort',
 'lista': 'msg_list fg_settings_list',
 'lista_numerada': 'msg_list_numbered',
 'cuadricula': 'msg_view_grid',
 'tarjeta': 'msg_payment_card',
 'microfono': 'input_mic input_mic_pressed flexy_composer_voice calls_unmute baseline_mic_16 baseline_mic_24 baseline_mic_96 baseline_keyboard_voice_24',
 'microfono_desactivado': 'calls_mute calls_mute_mini',
 'volumen': 'calls_speaker',
 'silencio': 'calls_speaker_off',
 'audifonos': 'calls_headphones calls_menu_headset',
 'reproducir': 'player_play player_new_play msg_play',
 'pausar': 'player_pause player_new_pause msg_pause',
 'detener': 'msg_stop',
 'repetir': 'player_new_repeat_off player_new_repeatall',
 'aleatorio': 'player_new_shuffle player_new_shuffle_off',
 'temporizador': 'msg_timer player_timer',
 'infinito': 'msg_infinite',
 'emoji': 'msg_emoji_smiles smiles_tab_smiles baseline_emoticon_24 baseline_emoticon_outline_24 baseline_emoji_symbols_24',
 'sticker': 'input_smile input_sticker msg_sticker msg_emoji_stickers smiles_tab_stickers flexy_composer_smile flexy_composer_sticker flexy_composer_folded',
 'gif': 'msg_gif',
 'adjuntar': 'input_attach flexy_composer_clip',
 'mensaje_texto': 'input_message',
 'ubicacion': 'msg_location bot_location menu_location baseline_location_on_16 baseline_location_on_18 baseline_location_on_20 baseline_location_on_24 baseline_location_on_48',
 'avion_papel': 'filter_airplane',
 'idioma': 'msg_language settings_language fg_settings_globe fg_settings_info fg_settings_comunidad settings3_info',
 'mencion': 'msg_mention menu_username baseline_alternate_email_12 baseline_alternate_email_24',
 'hashtag': 'menu_hashtag',
 'tipografia': 'msg_text',
 'traducir': 'msg_translate ic_translate',
 'llamada_saliente': 'baseline_call_made_18',
 'llamada_entrante': 'baseline_call_received_18',
 'llamada_perdida': 'baseline_call_missed_18',
 'llamada_agregar': 'msg_call_add',
 'videollamada_contacto': 'msg_video_contact',
 'compartir_pantalla': 'calls_sharescreen',
 'transmitir_pantalla': 'msg_cast',
 'monitor': 'device_desktop',
 'portatil': 'device_laptop',
 'telefono': 'device_phone',
 'dispositivos': 'settings_devices menu_devices baseline_devices_other_24 baseline_devices_other_96',
 'ayuda': 'msg_help settings_ask settings_faq baseline_help_16 baseline_help_24 baseline_help_outline_24',
 'informacion': 'msg_info baseline_info_24',
 'plugin': 'msg_plugins plugins_filled settings3_plugins fg_settings_plugins fg_settings_plugin baseline_extension_24',
 'archivo': 'msg_archive chats_archive',
 'sol': 'menu_day_mode_24', 'luna': 'menu_night_mode_24',
 'regalo': 'msg_gift menu_gift settings_gift',
 'base_datos': 'settings_data', 'codigo': 'msg_code', 'cubo': 'msg_box',
 'actualizar': 'msg_reset fg_settings_reset', 'agregar': 'msg_add baseline_add_24',
}

def mapping():
    dimensions = json.loads((ROOT/'tools/cupertino/mapping.json').read_text())
    names = {p.stem for p in RES.glob('drawable*/*') if p.is_file()}
    base = {name: icon for icon, group in GROUPS.items() for name in group.split()}
    result = {}
    for name in sorted(names):
        canonical = re.sub(r'_(remix|solar)$', '', name)
        icon = base.get(canonical)
        if icon is None:
            continue
        d = dimensions.get(name, {'width':24, 'height':24, 'color':0xff000000, 'mirrored':False})
        result[name] = dict(asset='fg_ios_'+icon, width=d['width'], height=d['height'], color=d['color'], mirrored=d['mirrored'])
    return result

def main():
    data = mapping()
    (ROOT/'tools/exact_icons/mapping.json').write_text(json.dumps(data, indent=2)+'\n')
    out = ['// Generated by tools/exact_icons/generate.py; reviewed semantic aliases only.',
           'package app.flexygram.icons;', 'import org.telegram.messenger.R;',
           'final class ExactIconMap {', ' private ExactIconMap() {}',
           ' static final class Entry {', '  final int id, asset, width, height, color; final boolean mirrored;',
           '  Entry(int i,int a,int w,int h,int c,boolean m){id=i;asset=a;width=w;height=h;color=c;mirrored=m;}', ' }',
           ' private static final class Holder {', '  static final Entry[] DATA=build();', ' }',
           ' static Entry get(int id){', '  if(id<=0)return null;', '  Entry[] data=Holder.DATA;int low=0,high=data.length-1;',
           '  while(low<=high){int mid=(low+high)>>>1,key=data[mid].id;if(key<id)low=mid+1;else if(key>id)high=mid-1;else return data[mid];}return null;', ' }',
           ' private static Entry[] build(){Entry[] data={']
    for name,d in data.items():
        out.append(f'  new Entry(R.drawable.{name},R.drawable.{d["asset"]},{d["width"]},{d["height"]},0x{d["color"]:08x},{str(d["mirrored"]).lower()}),')
    out += [' };java.util.Arrays.sort(data,(a,b)->Integer.compare(a.id,b.id));return data;}', '}']
    (ROOT/'TMessagesProj/src/main/java/app/flexygram/icons/ExactIconMap.java').write_text('\n'.join(out)+'\n')
    print(len(data), 'semantic aliases')

if __name__ == '__main__':
    main()
