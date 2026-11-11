#!/usr/bin/env python3
"""Actual Home list control sources against Android API37; native app services are explicit doubles. No APK."""
import os,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
JAVA=ROOT/'TMessagesProj/src/main/java'
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--android-jar',type=Path);parser.add_argument('--core-jar',type=Path);args=parser.parse_args()
sdk=args.android_jar or Path(os.environ.get('ANDROID_HOME',str(ROOT.parent/'.flexygram/android-sdk')))/'platforms/android-37.0/android.jar'
core=args.core_jar or Path(os.environ.get('FLEXY_CORE_JAR','/tmp/flexy-performance-libs/core.jar'))
if not sdk.is_file() or not core.is_file():raise SystemExit('Android API37 and AndroidX Core jar required.')
names=['HomeStyleConfig','HomeListSettingsActivity']
with tempfile.TemporaryDirectory(prefix='home-essentials-types-') as tmp:
 folder=Path(tmp);src=folder/'src';src.mkdir()
 def put(path,text):
  p=src/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
 code='\n'.join((JAVA/f'app/flexygram/home/{name}.java').read_text()for name in names)
 for name in names:put(f'app/flexygram/home/{name}.java',(JAVA/f'app/flexygram/home/{name}.java').read_text())
 strings=sorted(set(re.findall(r'R.string.(\w+)',code)));drawables=sorted(set(re.findall(r'R.drawable.(\w+)',code)));keys=sorted(set(re.findall(r'Theme.(key_\w+)',code)))
 put('org/telegram/messenger/R.java','package org.telegram.messenger;public class R{public static class string{'+''.join(f'public static int {n}={i};'for i,n in enumerate(strings))+'}public static class drawable{'+''.join(f'public static int {n}={i};'for i,n in enumerate(drawables))+'}}')
 put('org/telegram/ui/ActionBar/Theme.java','package org.telegram.ui.ActionBar;public class Theme{public interface ResourcesProvider{}public static int getColor(int k,ResourcesProvider p){return 0;}public static void applyCommonTheme(){}'+''.join(f'public static int {n}={i};'for i,n in enumerate(keys))+'}')
 put('org/telegram/messenger/ApplicationLoader.java','package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext;}')
 put('org/telegram/messenger/SharedConfig.java','package org.telegram.messenger;public class SharedConfig{public static boolean chatBlurEnabled(){return false;}}')
 put('org/telegram/messenger/AndroidUtilities.java','package org.telegram.messenger;public class AndroidUtilities{public static int dp(float n){return (int)n;}public static android.graphics.Typeface bold(){return null;}}')
 put('org/telegram/messenger/LocaleController.java','package org.telegram.messenger;public class LocaleController{public static boolean isRTL;public static String getString(int n){return "";}}')
 put('org/telegram/tgnet/TLRPC.java','package org.telegram.tgnet;public class TLRPC{public static class User{}}')
 put('org/telegram/messenger/ImageLocation.java','package org.telegram.messenger;public class ImageLocation{public static int TYPE_SMALL=0;public static ImageLocation getForUser(org.telegram.tgnet.TLRPC.User u,int type){return null;}}')
 put('org/telegram/ui/Components/AvatarDrawable.java','package org.telegram.ui.Components;public class AvatarDrawable extends android.graphics.drawable.ColorDrawable{public AvatarDrawable(org.telegram.tgnet.TLRPC.User u){}}')
 put('org/telegram/ui/Components/BackupImageView.java','package org.telegram.ui.Components;public class BackupImageView extends android.view.View{public BackupImageView(android.content.Context c){super(c);}public void setRoundRadius(int r){}public static class Receiver{public void setCurrentAccount(int n){}}public Receiver getImageReceiver(){return null;}public void setImage(org.telegram.messenger.ImageLocation l,String f,android.graphics.drawable.Drawable thumb,Object parent){}}')
 put('org/telegram/ui/Components/LayoutHelper.java','''package org.telegram.ui.Components;public class LayoutHelper{
 public static android.widget.FrameLayout.LayoutParams createFrame(int w,int h){return null;}
 public static android.widget.FrameLayout.LayoutParams createFrame(int w,int h,int gravity){return null;}
 public static android.widget.FrameLayout.LayoutParams createFrame(int w,int h,int gravity,int l,int t,int r,int b){return null;}
 public static android.widget.LinearLayout.LayoutParams createLinear(int w,int h,float weight,int l,int t,int r,int b){return null;}}
''')
 put('org/telegram/ui/Components/blur3/drawable/color/BlurredBackgroundColorProvider.java','package org.telegram.ui.Components.blur3.drawable.color;public interface BlurredBackgroundColorProvider{}')
 put('org/telegram/ui/Components/blur3/drawable/color/impl/BlurredBackgroundProviderImpl.java','package org.telegram.ui.Components.blur3.drawable.color.impl;public class BlurredBackgroundProviderImpl{public static boolean checkBlurEnabled(int a,org.telegram.ui.ActionBar.Theme.ResourcesProvider p){return false;}public static org.telegram.ui.Components.blur3.drawable.color.BlurredBackgroundColorProvider topPanel(org.telegram.ui.ActionBar.Theme.ResourcesProvider p){return null;}}')
 put('org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawable.java','package org.telegram.ui.Components.blur3.drawable;public class BlurredBackgroundDrawable extends android.graphics.drawable.ColorDrawable{public BlurredBackgroundDrawable setPadding(int n){return this;}public BlurredBackgroundDrawable setRadius(float n){return this;}public void updateColors(){}}')
 put('org/telegram/ui/Components/blur3/BlurredBackgroundDrawableViewFactory.java','package org.telegram.ui.Components.blur3;public class BlurredBackgroundDrawableViewFactory{public org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawable create(android.view.View v,org.telegram.ui.Components.blur3.drawable.color.BlurredBackgroundColorProvider p){return null;}}')
 put('androidx/recyclerview/widget/RecyclerView.java','package androidx.recyclerview.widget;public class RecyclerView{public static class ViewHolder{public android.view.View itemView;}}')
 put('org/telegram/ui/Cells/TextSettingsCell.java','package org.telegram.ui.Cells;public class TextSettingsCell extends android.view.View{public TextSettingsCell(android.content.Context c){super(c);}public void setTextAndValue(String a,String b,boolean divider){}}')
 put('org/telegram/ui/Cells/TextCheckCell.java','package org.telegram.ui.Cells;public class TextCheckCell extends android.view.View{public TextCheckCell(android.content.Context c){super(c);}public void setTextAndCheck(CharSequence t,boolean c,boolean d){}}')
 put('xyz/nextalone/nagram/NaConfig.java','package xyz.nextalone.nagram;public class NaConfig{public static final NaConfig INSTANCE=new NaConfig();public static class Config{public boolean Bool(){return false;}public void setConfigBool(boolean v){}}public Config getHideDividers(){return new Config();}}')
 put('app/exteraless/appearance/AppearanceConfig.java','package app.exteraless.appearance;public class AppearanceConfig{public static final int DIVIDER_LINE=1,DIVIDER_HIDDEN=0;public static class Config{public void setConfigInt(int n){}}public static final Config dividerStyle=new Config();public static int dividerStyle(){return 1;}public static void invalidateDividerStyle(){}}')
 put('org/telegram/ui/ActionBar/AlertDialog.java','package org.telegram.ui.ActionBar;public class AlertDialog{public static class Builder extends android.app.AlertDialog.Builder{public Builder(android.content.Context c,Theme.ResourcesProvider p){super(c);}}}')
 put('app/flexygram/settings/SignatureMatteSettingsActivity.java','''package app.flexygram.settings;public abstract class SignatureMatteSettingsActivity{
 protected static int TYPE_SETTINGS=1,TYPE_CHECK=2;protected org.telegram.ui.ActionBar.Theme.ResourcesProvider resourcesProvider;protected BaseListAdapter listAdapter;
 protected abstract String getActionBarTitle();protected void updateRows(){}protected int addRow(String key){return 0;}
 protected abstract BaseListAdapter createAdapter(android.content.Context c);protected void onItemClick(android.view.View v,int p,float x,float y){}
 protected android.app.Activity getParentActivity(){return null;}protected void showDialog(android.app.Dialog d){}
 public static class Navigation{public void rebuildFragments(int flags){}}protected Navigation getParentLayout(){return null;}
 protected abstract class BaseListAdapter{public int getItemViewType(int p){return 0;}public void onBindViewHolder(androidx.recyclerview.widget.RecyclerView.ViewHolder h,int p,boolean partial){}public boolean isEnabled(androidx.recyclerview.widget.RecyclerView.ViewHolder h){return true;}public void notifyItemChanged(int p){}}
 protected abstract class MatteListAdapter extends BaseListAdapter{protected MatteListAdapter(android.content.Context c){}}
 }''')
 libs=[sdk,core];annotation=core.parent/'annotation.jar'
 if annotation.is_file():libs.append(annotation)
 kotlin=core.parent/'kotlin.jar'
 if kotlin.is_file():libs.append(kotlin)
 subprocess.run(['javac','-proc:none','-cp',os.pathsep.join(map(str,libs)),'-d',str(folder/'classes'),*map(str,src.rglob('*.java'))],check=True)
print('Home list controls and legacy migration type checked against '+str(sdk)+' and AndroidX Core; app services are doubles. No APK built.')
