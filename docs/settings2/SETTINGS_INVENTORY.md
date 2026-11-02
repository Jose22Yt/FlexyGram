# Signature Settings 2.0 — source inventory

This is a source-level inventory, not device acceptance. Baseline: `0bfd01e748934b5eac2c6ba4215deb96119d6f5a`. The later official commit `e681972163c0f25df79b367be17d106ba76d8087` only changes DialogsActivity and is retained unchanged.

## Named rows

The 213 entries below identify presentation rows, including headers and navigation. An alias is a navigation identifier, **not necessarily a stored preference key**. Original OpenExtera click handlers remain byte-identical; the editor still owns its original ConfigItem/NaConfig/NekoConfig/AppearanceConfig/ChatsConfig and conditional logic. Anonymous dependent rows inherit their named owner's scope. `@moved` retires an old navigation entry; `@native` delegates to Telegram.

| Source / class | Field | Aliases | Canonical scope | Baseline method:line | Validation |
| --- | --- | --- | --- | --- | --- |
| appearance / OpenExteraAppearanceActivity | avatarsHeaderRow | matteAvatarsHeader | avatars | updateRows:151 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | avatarCornersPreviewRow | avatarCorners | avatars | updateRows:152 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | singleCornerRadiusRow | singleCornerRadius | avatars | updateRows:153 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | chatListHeaderRow | chatListHeader | chat_list | updateRows:156 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | chatListPreviewRow | chatListPreview | chat_list | updateRows:157 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | forceSnowRow | forceSnow | chat_list | updateRows:158 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | centerTitleRow | centerTitle | chat_list | updateRows:159 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | senderMiniAvatarsRow | senderMiniAvatars | chat_list | updateRows:160 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | titleTextRow | titleText | chat_list | updateRows:161 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | foldersHeaderRow | foldersHeader | folders | updateRows:164 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | foldersPreviewRow | foldersPreview | folders | updateRows:165 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | folderThemeAccentRow | folderThemeAccent | folders | updateRows:166 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | tabTitleStyleRow | tabTitleStyle | folders | updateRows:167 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | tabCounterRow | tabCounter | folders | updateRows:168 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | iconsHeaderRow | matteIconsHeader | @moved | updateRows:171 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | iconPacksRow | iconPacks | @moved | updateRows:172 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | emojiSetsRow | emojiSets, EmojiSets | @moved | updateRows:173 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | linksHeaderRow | linksHeader | @moved | updateRows:176 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | bottomTabsRow | bottomTabs | @moved | updateRows:177 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | appNavigationRow | appNavigation | @moved | updateRows:178 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | pillStackRow | pillStack | @moved | updateRows:179 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | hidingRow | hiding | @moved | updateRows:180 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | appearanceHeaderRow | appearanceHeader | fonts | updateRows:183 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | fabShapeRow | fabShape | chat_list | updateRows:184 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | useSystemFontsRow | useSystemFonts | fonts | updateRows:185 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | customThemesRow | customThemes | effects | updateRows:186 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | sectionsHeaderRow | sectionsHeader | effects | updateRows:189 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | sectionRadiusRow | sectionRadius | effects | updateRows:190 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | separateHeadersRow | separateHeaders | effects | updateRows:191 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | dividerStyleRow | dividerStyle | effects | updateRows:192 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | blurHeaderRow | blurHeader | effects | updateRows:195 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | gooeyAvatarRow | gooeyAvatar | avatars | updateRows:196 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | glassOutlineRow | glassOutline | effects | updateRows:197 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | glassMessageMenuRow | glassMessageMenu | effects | updateRows:198 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | forceBlurRow | forceBlur | effects | updateRows:199 | Source policy; device pending |
| appearance / OpenExteraAppearanceActivity | disableAvatarBlurRow | disableAvatarBlur | avatars | updateRows:200 | Source policy; device pending |
| general / OpenExteraGeneralActivity | translateHeaderRow | translateHeader | translation_options | updateRows:174 | Source policy; device pending |
| general / OpenExteraGeneralActivity | translatorRow | translator | @moved | updateRows:175 | Source policy; device pending |
| general / OpenExteraGeneralActivity | translateInSheetRow | translateInSheet | translation_options | updateRows:176 | Source policy; device pending |
| general / OpenExteraGeneralActivity | generalHeaderRow | generalHeader | general | updateRows:179 | Source policy; device pending |
| general / OpenExteraGeneralActivity | disableNumberRoundingRow | disableNumberRounding | general | updateRows:180 | Source policy; device pending |
| general / OpenExteraGeneralActivity | formatTimeWithSecondsRow | formatTimeWithSeconds | general | updateRows:181 | Source policy; device pending |
| general / OpenExteraGeneralActivity | inAppVibrationRow | inAppVibration | general | updateRows:182 | Source policy; device pending |
| general / OpenExteraGeneralActivity | filterZalgoRow | filterZalgo | general | updateRows:183 | Source policy; device pending |
| general / OpenExteraGeneralActivity | speedHeaderRow | speedHeader | general | updateRows:186 | Source policy; device pending |
| general / OpenExteraGeneralActivity | downloadSpeedRow | downloadSpeed | general | updateRows:187 | Source policy; device pending |
| general / OpenExteraGeneralActivity | uploadBoostRow | uploadBoost | general | updateRows:188 | Source policy; device pending |
| general / OpenExteraGeneralActivity | useIPv6Row | IPv6 | general | updateRows:190 | Source policy; device pending |
| general / OpenExteraGeneralActivity | dnsTypeRow | dnsType, DnsType | general | updateRows:191 | Source policy; device pending |
| general / OpenExteraGeneralActivity | customDoHRow | customDoH, CustomDoH | general | updateRows:192 | Source policy; device pending |
| general / OpenExteraGeneralActivity | storageHeaderRow | storageHeader | files | updateRows:196 | Source policy; device pending |
| general / OpenExteraGeneralActivity | saveToChatSubfolderRow | saveToChatSubfolder, SaveToChatSubfolder | files | updateRows:197 | Source policy; device pending |
| general / OpenExteraGeneralActivity | savePathRow | savePath | files | updateRows:198 | Source policy; device pending |
| general / OpenExteraGeneralActivity | profileHeaderRow | profileHeader | profile | updateRows:201 | Source policy; device pending |
| general / OpenExteraGeneralActivity | relativeLastSeenRow | relativeLastSeen | profile | updateRows:202 | Source policy; device pending |
| general / OpenExteraGeneralActivity | hidePhoneRow | hidePhone | profile | updateRows:203 | Source policy; device pending |
| general / OpenExteraGeneralActivity | showIdAndDcRow | showIdAndDc | profile | updateRows:204 | Source policy; device pending |
| general / OpenExteraGeneralActivity | lastfmRow | lastfm | profile | updateRows:205 | Source policy; device pending |
| general / OpenExteraGeneralActivity | archiveHeaderRow | archiveHeader | archive | updateRows:208 | Source policy; device pending |
| general / OpenExteraGeneralActivity | sortByUnreadRow | sortByUnread, SortByUnread | archive | updateRows:209 | Source policy; device pending |
| general / OpenExteraGeneralActivity | unlimitedPinnedRow | unlimitedPinnedDialogs, UnlimitedPinnedDialogs | archive | updateRows:210 | Source policy; device pending |
| general / OpenExteraGeneralActivity | hideArchiveRow | hideArchive | archive | updateRows:211 | Source policy; device pending |
| general / OpenExteraGeneralActivity | archiveOnPullRow | archiveOnPull | archive | updateRows:214 | Source policy; device pending |
| general / OpenExteraGeneralActivity | disableUnarchiveSwipeRow | disableUnarchiveSwipe | archive | updateRows:215 | Source policy; device pending |
| general / OpenExteraGeneralActivity | mapsHeaderRow | mapsHeader | general | updateRows:218 | Source policy; device pending |
| general / OpenExteraGeneralActivity | mapProviderRow | mapProvider | general | updateRows:219 | Source policy; device pending |
| general / OpenExteraGeneralActivity | mapDriftingFixRow | mapDriftingFix | general | updateRows:220 | Source policy; device pending |
| general / OpenExteraGeneralActivity | mapPreviewRow | mapPreview | general | updateRows:221 | Source policy; device pending |
| general / OpenExteraGeneralActivity | notificationsHeaderRow | notificationsHeader | general | updateRows:224 | Source policy; device pending |
| general / OpenExteraGeneralActivity | pushServiceTypeRow | pushServiceType, PushServiceType | general | updateRows:225 | Source policy; device pending |
| general / OpenExteraGeneralActivity | notificationBubblesRow | disableNotificationBubbles | general | updateRows:231 | Source policy; device pending |
| general / OpenExteraGeneralActivity | pushStatusRow | pushStatus | general | updateRows:232 | Source policy; device pending |
| general / OpenExteraGeneralActivity | batteryOptimizationRow | batteryOptimization | general | updateRows:233 | Source policy; device pending |
| general / OpenExteraGeneralActivity | glyphRow | glyph | general | updateRows:234 | Source policy; device pending |
| chats / OpenExteraChatsActivity | flexyBubblesRow | flexyBubbles | @moved | updateSignatureHubRows:443 | Source policy; device pending |
| chats / OpenExteraChatsActivity | signatureHeaderRow | signatureChatHeader | @moved | updateSignatureHubRows:444 | Source policy; device pending |
| chats / OpenExteraChatsActivity | composerSettingsRow | flexyComposerSettings | @moved | updateSignatureHubRows:445 | Source policy; device pending |
| chats / OpenExteraChatsActivity | signatureThemeRow | flexyThemeWallpaper | @moved | updateSignatureHubRows:446 | Source policy; device pending |
| chats / OpenExteraChatsActivity | smartPreviewsRow | flexySmartPreviews | @moved | updateSignatureHubRows:447 | Source policy; device pending |
| chats / OpenExteraChatsActivity | flexyContextPanelRow | flexyContextPanel | @moved | updateSignatureHubRows:449 | Source policy; device pending |
| chats / OpenExteraChatsActivity | signatureMessagesRow | flexyMessagesGestures | @moved | updateSignatureHubRows:450 | Source policy; device pending |
| chats / OpenExteraChatsActivity | signatureStickersRow | flexyStickersMedia | @moved | updateSignatureHubRows:451 | Source policy; device pending |
| chats / OpenExteraChatsActivity | chatSettingsRow | chatSettings | @moved | updateSignatureHubRows:453 | Source policy; device pending |
| chats / OpenExteraChatsActivity | stickerSizeRow | stickerSize | stickers | updateStickerRows:457 | Source policy; device pending |
| chats / OpenExteraChatsActivity | stickerTimeRow | stickerTime, hideTimeOnStickers | stickers | updateStickerRows:458 | Source policy; device pending |
| chats / OpenExteraChatsActivity | repliesGroupRow | replies | stickers | updateStickerRows:459 | Source policy; device pending |
| chats / OpenExteraChatsActivity | stickerShapeHeaderRow | stickerShapeHeader | stickers | updateStickerRows:469 | Source policy; device pending |
| chats / OpenExteraChatsActivity | stickerShapeRow | stickerShape | stickers | updateStickerRows:470 | Source policy; device pending |
| chats / OpenExteraChatsActivity | stickersHeaderRow | stickersHeader | stickers | updateStickerRows:473 | Source policy; device pending |
| chats / OpenExteraChatsActivity | unlimitedGroupRow | unlimited, unlimitedRecentStickers | stickers | updateStickerRows:475 | Source policy; device pending |
| chats / OpenExteraChatsActivity | mediaRow | media | @moved | updateStickerRows:484 | Source policy; device pending |
| chats / OpenExteraChatsActivity | linksHeaderRow | linksHeader | @moved | updateChatRows:488 | Source policy; device pending |
| chats / OpenExteraChatsActivity | menusRow | menus | @moved | updateChatRows:489 | Source policy; device pending |
| chats / OpenExteraChatsActivity | flexyContextPanelRow | flexyContextPanel | @moved | updateChatRows:490 | Source policy; device pending |
| chats / OpenExteraChatsActivity | mediaRow | media | @moved | updateChatRows:491 | Source policy; device pending |
| chats / OpenExteraChatsActivity | aiChatRow | aiChat | @moved | updateChatRows:492 | Source policy; device pending |
| chats / OpenExteraChatsActivity | inputHeaderRow | inputHeader | messages | updateChatRows:497 | Source policy; device pending |
| chats / OpenExteraChatsActivity | addCommaRow | addCommaAfterMention | messages | updateChatRows:498 | Source policy; device pending |
| chats / OpenExteraChatsActivity | inlineMathRow | inlineMathResult | messages | updateChatRows:499 | Source policy; device pending |
| chats / OpenExteraChatsActivity | inlineMathCurrencyRow | inlineMathCurrency | messages | updateChatRows:500 | Source policy; device pending |
| chats / OpenExteraChatsActivity | tapToSwitchRecordRow | tapToSwitchRecord, UseChatAttachEnterMenu | messages | updateChatRows:501 | Source policy; device pending |
| chats / OpenExteraChatsActivity | keepAttachButtonRow | keepAttachButton | messages | updateChatRows:502 | Source policy; device pending |
| chats / OpenExteraChatsActivity | doubleTapHeaderRow | doubleTapHeader | gestures | updateChatRows:505 | Source policy; device pending |
| chats / OpenExteraChatsActivity | doubleTapRow | doubleTapPreview | gestures | updateChatRows:506 | Source policy; device pending |
| chats / OpenExteraChatsActivity | doubleTapIncomingRow | doubleTapIncoming | gestures | updateChatRows:507 | Source policy; device pending |
| chats / OpenExteraChatsActivity | doubleTapOutgoingRow | doubleTapOutgoing | gestures | updateChatRows:508 | Source policy; device pending |
| chats / OpenExteraChatsActivity | doubleTapReactionRow | doubleTapReaction | gestures | updateChatRows:511 | Source policy; device pending |
| chats / OpenExteraChatsActivity | chatsHeaderRow | chatsHeader | messages | updateChatRows:517 | Source policy; device pending |
| chats / OpenExteraChatsActivity | quickTransitionGroupRow | quickTransition | gestures | updateChatRows:518 | Source policy; device pending |
| chats / OpenExteraChatsActivity | deleteChatForBothSidesRow | deleteChatForBothSides, DeleteChatForBothSides | messages | updateChatRows:525 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hideKeyboardOnScrollRow | hideKeyboardOnScroll | gestures | updateChatRows:526 | Source policy; device pending |
| chats / OpenExteraChatsActivity | searchHeaderRow | searchHeader | messages | updateChatRows:529 | Source policy; device pending |
| chats / OpenExteraChatsActivity | disableGlobalSearchRow | disableGlobalSearch | messages | updateChatRows:530 | Source policy; device pending |
| chats / OpenExteraChatsActivity | searchHashtagChatRow | searchHashtagChat, SearchHashtagDefaultPageChat | messages | updateChatRows:531 | Source policy; device pending |
| chats / OpenExteraChatsActivity | searchHashtagChannelRow | searchHashtagChannel, SearchHashtagDefaultPageChannel | messages | updateChatRows:532 | Source policy; device pending |
| chats / OpenExteraChatsActivity | messagesHeaderRow | messagesHeader | messages | updateChatRows:535 | Source policy; device pending |
| chats / OpenExteraChatsActivity | removeMessageTailRow | removeMessageTail | post_appearance | updateChatRows:536 | Source policy; device pending |
| chats / OpenExteraChatsActivity | replaceEditedRow | replaceEdited | messages | updateChatRows:537 | Source policy; device pending |
| chats / OpenExteraChatsActivity | showOnlineStatusRow | showOnlineStatus | messages | updateChatRows:538 | Source policy; device pending |
| chats / OpenExteraChatsActivity | showResultsBeforeVotingRow | showResultsBeforeVoting | messages | updateChatRows:539 | Source policy; device pending |
| chats / OpenExteraChatsActivity | dateOfForwardedMsgRow | dateOfForwardedMsg, DateOfForwardedMsg | messages | updateChatRows:540 | Source policy; device pending |
| chats / OpenExteraChatsActivity | showTimeHintRow | showTimeHint, ShowTimeHint | messages | updateChatRows:541 | Source policy; device pending |
| chats / OpenExteraChatsActivity | rememberAllRepliesRow | rememberAllBackMessages, rememberAllBackMessages | messages | updateChatRows:542 | Source policy; device pending |
| chats / OpenExteraChatsActivity | linkConfirmationsHeaderRow | linkConfirmationsHeader | messages | updateChatRows:545 | Source policy; device pending |
| chats / OpenExteraChatsActivity | fixLinkPreviewRow | fixLinkPreview, FixLinkPreview | messages | updateChatRows:546 | Source policy; device pending |
| chats / OpenExteraChatsActivity | disableLinkPreviewRow | disableLinkPreviewByDefault, DisableLinkPreviewByDefault | messages | updateChatRows:547 | Source policy; device pending |
| chats / OpenExteraChatsActivity | openLinkConfirmationRow | openLinkConfirmation, SkipOpenLinkConfirm, ConfirmAllLinks | messages | updateChatRows:548 | Source policy; device pending |
| chats / OpenExteraChatsActivity | stripTrackingGroupRow | stripTracking | messages | updateChatRows:559 | Source policy; device pending |
| chats / OpenExteraChatsActivity | trackingFilterRow | trackingFilter | messages | updateChatRows:566 | Source policy; device pending |
| chats / OpenExteraChatsActivity | channelPostsHeaderRow | channelPostsHeader | post_appearance | updateChatRows:569 | Source policy; device pending |
| chats / OpenExteraChatsActivity | wideChannelPostsPreviewRow | wideChannelPostsPreview | post_appearance | updateChatRows:570 | Source policy; device pending |
| chats / OpenExteraChatsActivity | wideChannelPostsRow | wideChannelPosts | post_appearance | updateChatRows:571 | Source policy; device pending |
| chats / OpenExteraChatsActivity | wideFeedPostsRow | wideFeedPosts | post_appearance | updateChatRows:572 | Source policy; device pending |
| chats / OpenExteraChatsActivity | buttonsHeaderRow | buttonsHeader | menus | updateMenuRows:577 | Source policy; device pending |
| chats / OpenExteraChatsActivity | bottomButtonRow | bottomButton | menus | updateMenuRows:578 | Source policy; device pending |
| chats / OpenExteraChatsActivity | adminShortcutsRow | adminShortcuts | menus | updateMenuRows:579 | Source policy; device pending |
| chats / OpenExteraChatsActivity | menusHeaderRow | menusHeader | menus | updateMenuRows:582 | Source policy; device pending |
| chats / OpenExteraChatsActivity | chatMenuGroupRow | chatMenu | menus | updateMenuRows:583 | Source policy; device pending |
| chats / OpenExteraChatsActivity | groupedMessageMenuRow | groupedMessageMenu | menus | updateMenuRows:605 | Source policy; device pending |
| chats / OpenExteraChatsActivity | messageMenuGroupRow | messageMenu | menus | updateMenuRows:606 | Source policy; device pending |
| chats / OpenExteraChatsActivity | textStyleRow | textStyle, TextStyle | menus | updateMenuRows:640 | Source policy; device pending |
| chats / OpenExteraChatsActivity | mediaViewerMenuGroupRow | mediaViewerMenu | menus | updateMenuRows:641 | Source policy; device pending |
| chats / OpenExteraChatsActivity | actionBarButtonsGroupRow | actionBarButtons | menus | updateMenuRows:653 | Source policy; device pending |
| chats / OpenExteraChatsActivity | deleteMenuGroupRow | defaultDeleteMenu, DefaultDeleteMenu | menus | updateMenuRows:664 | Source policy; device pending |
| chats / OpenExteraChatsActivity | cameraHeaderRow | cameraHeader | media | updateMediaRows:677 | Source policy; device pending |
| chats / OpenExteraChatsActivity | cameraTypeRow | cameraType | media | updateMediaRows:678 | Source policy; device pending |
| chats / OpenExteraChatsActivity | extendedSettingsGroupRow | extendedSettings | media | updateMediaRows:684 | Source policy; device pending |
| chats / OpenExteraChatsActivity | videoMessagesCameraRow | videoMessagesCamera | media | updateMediaRows:705 | Source policy; device pending |
| chats / OpenExteraChatsActivity | rememberLastUsedCameraRow | rememberLastUsedCamera | media | updateMediaRows:708 | Source policy; device pending |
| chats / OpenExteraChatsActivity | zoomSliderRow | zoomSlider | media | updateMediaRows:712 | Source policy; device pending |
| chats / OpenExteraChatsActivity | staticZoomRow | staticZoom | media | updateMediaRows:713 | Source policy; device pending |
| chats / OpenExteraChatsActivity | photoHeaderRow | photoHeader | media | updateMediaRows:716 | Source policy; device pending |
| chats / OpenExteraChatsActivity | alwaysSendHdRow | alwaysSendInHD | media | updateMediaRows:717 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hdrPhotosRow | hdrPhotos | media | updateMediaRows:718 | Source policy; device pending |
| chats / OpenExteraChatsActivity | disableInstantCameraRow | disableInstantCamera, DisableInstantCamera | media | updateMediaRows:719 | Source policy; device pending |
| chats / OpenExteraChatsActivity | videosHeaderRow | videosHeader | media | updateMediaRows:722 | Source policy; device pending |
| chats / OpenExteraChatsActivity | preferOriginalQualityRow | preferOriginalQuality | media | updateMediaRows:723 | Source policy; device pending |
| chats / OpenExteraChatsActivity | enhancedVideoBitrateRow | enhancedVideoBitrate, EnhancedVideoBitrate | media | updateMediaRows:724 | Source policy; device pending |
| chats / OpenExteraChatsActivity | videoPlayerDecoderRow | videoPlayerDecoder, VideoPlayerDecoder | media | updateMediaRows:725 | Source policy; device pending |
| chats / OpenExteraChatsActivity | showSmallGifRow | showSmallGIF, ShowSmallGIF | media | updateMediaRows:726 | Source policy; device pending |
| chats / OpenExteraChatsActivity | playbackHeaderRow | playbackHeader | media | updateMediaRows:729 | Source policy; device pending |
| chats / OpenExteraChatsActivity | doubleTapSeekDurationRow | doubleTapSeekDuration | media | updateMediaRows:730 | Source policy; device pending |
| chats / OpenExteraChatsActivity | swipeToPipRow | swipeToPip | media | updateMediaRows:731 | Source policy; device pending |
| chats / OpenExteraChatsActivity | unmuteWithVolumeButtonsRow | unmuteWithVolumeButtons | media | updateMediaRows:732 | Source policy; device pending |
| chats / OpenExteraChatsActivity | pauseGroupRow | pauseOnMinimize | media | updateMediaRows:733 | Source policy; device pending |
| chats / OpenExteraChatsActivity | voiceHeaderRow | voiceHeader | media | updateMediaRows:743 | Source policy; device pending |
| chats / OpenExteraChatsActivity | voiceEnhancementsRow | noiseSuppressAndVoiceEnhance, NoiseSuppressAndVoiceEnhance | media | updateMediaRows:744 | Source policy; device pending |
| chats / OpenExteraChatsActivity | dontAutoPlayNextVoiceRow | dontAutoPlayNextVoice, DontAutoPlayNextVoice | media | updateMediaRows:745 | Source policy; device pending |
| chats / OpenExteraChatsActivity | disableProximityEventsRow | disableProximityEvents, DisableProximityEvents | media | updateMediaRows:746 | Source policy; device pending |
| chats / OpenExteraChatsActivity | transcribeHeaderRow | transcribeHeader | media | updateMediaRows:749 | Source policy; device pending |
| chats / OpenExteraChatsActivity | transcribeProviderRow | transcribeProvider, TranscribeProviderShort | media | updateMediaRows:750 | Source policy; device pending |
| chats / OpenExteraChatsActivity | cloudflareCredentialsRow | cloudflareCredentials, CloudflareCredentials | media | updateMediaRows:751 | Source policy; device pending |
| chats / OpenExteraChatsActivity | geminiApiKeyRow | llmProviderGeminiKey, LlmProviderGeminiKey | media | updateMediaRows:752 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hidingChatListHeaderRow | hidingChatListHeader | visible | updateHidingRows:761 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hideActionBarStatusRow | hideActionBarStatus | visible | updateHidingRows:762 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hideStoriesRow | hideStories, HideStoriesFromHeader, DisableStories | visible | updateHidingRows:763 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hideFloatingButtonRow | hideFloatingButton | visible | updateHidingRows:764 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hideSearchBarRow | hideSearchBar | visible | updateHidingRows:765 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hideAllChatsRow | hideAllChats | visible | updateHidingRows:766 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hidingChatsHeaderRow | hidingChatsHeader | visible | updateHidingRows:769 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hideSendAsPeerRow | hideSendAsPeer | visible | updateHidingRows:770 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hideShareButtonRow | hideShareButton | visible | updateHidingRows:771 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hideGiftButtonRow | hideGiftButton | visible | updateHidingRows:772 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hideSearchButtonRow | hideSearchButton | visible | updateHidingRows:773 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hideReactionsGroupRow | hideReactions | visible | updateHidingRows:774 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hideCameraTileRow | hideCameraTile | visible | updateHidingRows:782 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hidingStickersHeaderRow | hidingStickersHeader | visible | updateHidingRows:785 | Source policy; device pending |
| chats / OpenExteraChatsActivity | disableTrendingRow | disableTrending, DisableTrending | visible | updateHidingRows:786 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hideGroupStickerRow | hideGroupSticker | visible | updateHidingRows:787 | Source policy; device pending |
| chats / OpenExteraChatsActivity | disableGreetingRow | disableGreeting | visible | updateHidingRows:788 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hidingAiHeaderRow | hidingAiHeader | visible | updateHidingRows:791 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hideAiGroupRow | hideAi | visible | updateHidingRows:792 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hideAiEditorRow | hideAiEditor | visible | updateHidingRows:794 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hideAiSummaryRow | hideAiSummary | visible | updateHidingRows:795 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hideAiIvRow | hideAiIv | visible | updateHidingRows:796 | Source policy; device pending |
| chats / OpenExteraChatsActivity | premiumElementsGroupRow | premiumElements, PremiumElements | visible | updateHidingRows:800 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hidingSettingsHeaderRow | hidingSettingsHeader | visible | updateHidingRows:816 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hideSettingsGroupRow | hideSettingsSections, HidePremiumSection, HideHelpSection | visible | updateHidingRows:817 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hidePremiumSectionRow | hidePremiumSection, HidePremiumSection | visible | updateHidingRows:819 | Source policy; device pending |
| chats / OpenExteraChatsActivity | hideHelpSectionRow | hideHelpSection, HideHelpSection | visible | updateHidingRows:820 | Source policy; device pending |
| other / OpenExteraOtherActivity | googleHeaderRow | googleHeader | advanced | updateRows:131 | Source policy; device pending |
| other / OpenExteraOtherActivity | crashReportsRow | crashReports | advanced | updateRows:132 | Source policy; device pending |
| other / OpenExteraOtherActivity | contentCaptureRow | contentCapture | advanced | updateRows:133 | Source policy; device pending |
| other / OpenExteraOtherActivity | nagramHeaderRow | nagramHeader | advanced | updateRows:136 | Source policy; device pending |
| other / OpenExteraOtherActivity | ayuMomentsRow | ayuMoments | advanced | updateRows:138 | Source policy; device pending |
| other / OpenExteraOtherActivity | experimentalHeaderRow | experimentalHeader | advanced | updateRows:141 | Source policy; device pending |
| other / OpenExteraOtherActivity | localPremiumRow | localPremium | advanced | updateRows:142 | Source policy; device pending |
| other / OpenExteraOtherActivity | sensitiveContentRow | sensitiveDisableFiltering, SensitiveDisableFiltering | advanced | updateRows:146 | Source policy; device pending |
| other / OpenExteraOtherActivity | backupHeaderRow | backupHeader | advanced | updateRows:149 | Source policy; device pending |
| other / OpenExteraOtherActivity | exportEtgRow | exportEtgSettings | advanced | updateRows:150 | Source policy; device pending |
| other / OpenExteraOtherActivity | importEtgRow | importEtgSettings | advanced | updateRows:151 | Source policy; device pending |
| other / OpenExteraOtherActivity | resetSettingsRow | resetSettings | advanced | updateRows:157 | Source policy; device pending |
| other / OpenExteraOtherActivity | deleteAccountRow | deleteAccount | @native | updateRows:158 | Source policy; device pending |

## Original ConfigCells

These are existing ConfigCells, not new controls. Config references and stored key names are retained; `retired` below means not repeated on the residual Neko page because its canonical editor owns it (or was already retired upstream). This does not delete its stored value. Source inspection does not establish runtime persistence for every entry.

| Class:line / field | Original key / ConfigItem references | Residual route | Excluded from residual | Validation |
| --- | --- | --- | --- | --- |
| NekoGeneralSettingsActivity:87 / customTitleRow | CustomTitle / CustomTitle | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:90 / folderNameAsTitleRow | FolderNameAsTitle / FolderNameAsTitle | appearance_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:91 / customTitleUserNameRow | CustomTitleUserName / CustomTitleUserName | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:92 / disableNumberRoundingRow | DisableNumberRounding / DisableNumberRounding | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:93 / preferCommonGroupsTabRow | PreferCommonGroupsTab / PreferCommonGroupsTab | general_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:94 / usePersianCalendarRow | UsePersianCalendar / UsePersianCalendar | general_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:95 / displayPersianCalendarByLatinRow | DisplayPersianCalendarByLatin / DisplayPersianCalendarByLatin | general_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:96 / showIdAndDcRow | IdDcType / IdDcType | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:101 / nameOrderRow | NameOrder / NameOrder | general_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:109 / saveToChatSubfolderRow | SaveToChatSubfolder / SaveToChatSubfolder | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:110 / customSavePathRow | customSavePath / customSavePath | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:122 / useIPv6Row | IPv6 / IPv6 | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:123 / defaultHlsVideoQualityRow | DefaultHlsVideoQuality / DefaultHlsVideoQuality | media_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:131 / dnsTypeRow | DnsType / DnsType | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:137 / customDoHRow | CustomDoH / CustomDoH | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:142 / useOSMDroidMapRow | useOSMDroidMap / useOSMDroidMap | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:143 / mapDriftingFixForGoogleMapsRow | mapDriftingFixForGoogleMaps / mapDriftingFixForGoogleMaps | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:144 / mapPreviewRow | MapPreviewProvider / MapPreviewProvider | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:153 / hideAllTabRow | HideAllTab / HideAllTab | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:154 / doNotUnarchiveBySwipeRow | DoNotUnarchiveBySwipe / DoNotUnarchiveBySwipe | navigation_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:155 / openArchiveOnPullRow | OpenArchiveOnPull / OpenArchiveOnPull | advanced_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:156 / hideArchiveRow | HideArchive / HideArchive | advanced_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:157 / ignoreUnreadCountRow | IgnoreUnreadCount / IgnoreUnreadCount | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:162 / tabsTitleTypeRow | TabTitleType / TabTitleType | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:171 / sortByUnreadRow | SortByUnread / SortByUnread | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:172 / hideDialogsSearchFieldRow | HideDialogsSearchField / HideDialogsSearchField | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:173 / disableDialogsFloatingButtonRow | DisableDialogsFloatingButton / DisableDialogsFloatingButton | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:174 / disableBotOpenButtonRow | DisableBotOpenButton / DisableBotOpenButton | general_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:175 / mediaPreviewRow | MediaPreview / MediaPreview | media_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:180 / typefaceRow | TypefaceUseDefault / TypefaceUseDefault | appearance_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:181 / alwaysShowDownloadIconRow | AlwaysShowDownloadIcon / AlwaysShowDownloadIcon | appearance_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:182 / showStickersInTopLevelRow | ShowStickersRowToplevel / ShowStickersRowToplevel | stickers_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:183 / hidePremiumSectionRow | HidePremiumSection / HidePremiumSection | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:184 / hideHelpSectionRow | HideHelpSection / HideHelpSection | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:185 / iconReplacements | IconReplacements / IconReplacements | appearance_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:192 / switchStyleRow | SwitchStyle / SwitchStyle | appearance_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:197 / sliderStyleRow | SliderStyle / SliderStyle | appearance_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:202 / actionBarDecorationRow | ActionBarDecoration / ActionBarDecoration | appearance_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:208 / chatDecorationRow | ChatDecoration / ChatDecoration | appearance_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:213 / notificationIconRow | NotificationIcon / NotificationIcon | general_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:217 / tabletModeRow | TabletMode / TabletMode | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:222 / centerActionBarTitleRow | CenterActionBarTitleType / CenterActionBarTitleType | appearance_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:232 / strokeOnViews | StrokeOnViews / StrokeOnViews | general_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:233 / disableAvatarBlurRow | DisableAvatarBlur / DisableAvatarBlur | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:238 / hideTitlesRow | MainTabsHideTitles / MainTabsHideTitles | navigation_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:239 / hideContactsRow | MainTabsHideContacts / MainTabsHideContacts | navigation_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:240 / hideCallsSettingsRow | MainTabsHideCallsSettings / MainTabsHideCallsSettings | navigation_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:241 / hideProfileRow | MainTabsHideProfile / MainTabsHideProfile | navigation_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:242 / hideBottomNavigationBarRow | HideBottomNavigationBar / HideBottomNavigationBar | navigation_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:247 / hidePhoneRow | HidePhone / HidePhone | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:248 / disableSystemAccountRow | DisableSystemAccount / DisableSystemAccount | advanced_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:249 / disableCrashlyticsCollectionRow | DisableCrashlyticsCollection / DisableCrashlyticsCollection | advanced_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:254 / pushServiceTypeRow | PushServiceType / PushServiceType | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:260 / pushServiceTypeUnifiedGatewayRow | PushServiceTypeUnifiedGateway / PushServiceTypeUnifiedGateway | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:261 / pushServiceTypeInAppDialogRow | PushServiceTypeInAppDialog / PushServiceTypeInAppDialog | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:262 / disableNotificationBubblesRow | disableNotificationBubbles / disableNotificationBubbles | general_extra | True | Source ownership; device pending |
| NekoGeneralSettingsActivity:267 / win32Row | Win32ExecutableFiles / Win32ExecutableFiles | advanced_extra | False | Source ownership; device pending |
| NekoGeneralSettingsActivity:268 / archiveRow | ArchiveFiles / ArchiveFiles | advanced_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:86 / stickerSizeRow | StickerSize / StickerSize | stickers_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:87 / showTimeHintRow | ShowTimeHint / ShowTimeHint | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:88 / hideTimeForStickerRow | HideTimeForSticker / HideTimeForSticker | stickers_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:89 / disableReplyBackgroundRow | MessageColoredBackground / MessageColoredBackground | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:94 / emojiSetsRow | EmojiSets / EmojiSets | stickers_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:95 / premiumElementsToggleRow | PremiumItemEmojiStatus / PremiumItemEmojiStatus, PremiumItemEmojiInReplies, PremiumItemCustomColorInReplies, PremiumItemCustomWallpaper, PremiumItemVideoAvatar, PremiumItemStarInReactions, PremiumItemStickerEffects, PremiumItemBoosts | stickers_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:106 / unreadBadgeOnBackButton | unreadBadgeOnBackButton / unreadBadgeOnBackButton | messages_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:107 / sendCommentAfterForwardRow | SendCommentAfterForward / SendCommentAfterForward | messages_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:108 / useChatAttachMediaMenuRow | UseChatAttachEnterMenu / UseChatAttachEnterMenu | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:109 / fixLinkPreviewRow | FixLinkPreview / FixLinkPreview | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:110 / disableLinkPreviewByDefaultRow | DisableLinkPreviewByDefault / DisableLinkPreviewByDefault | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:111 / deleteChatForBothSidesRow | DeleteChatForBothSides / DeleteChatForBothSides | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:112 / showMessageIDRow | ShowMessageID / ShowMessageID | messages_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:113 / showSeconds | showSeconds / showSeconds | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:114 / useEditedIconRow | UseEditedIcon / UseEditedIcon | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:115 / customEditedMessageRow | CustomEditedMessage / CustomEditedMessage | messages_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:116 / dateOfForwardMsgRow | DateOfForwardedMsg / DateOfForwardedMsg | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:117 / showFullAboutRow | ShowFullAbout / ShowFullAbout | messages_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:118 / disableTrendingRow | DisableTrending / DisableTrending | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:119 / disableZalgoSymbolsRow | ZalgoFilter / ZalgoFilter | advanced_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:120 / showOnlineStatusRow | ShowOnlineStatus / ShowOnlineStatus | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:121 / leftButtonActionRow | LeftBottomButtonAction / LeftBottomButtonAction | messages_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:138 / markdownParserRow | MarkdownParser / MarkdownParser | messages_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:146 / doubleTapActionRow | DoubleTapIncoming / DoubleTapIncoming | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:147 / doubleTapActionOutRow | DoubleTapOutgoing / DoubleTapOutgoing | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:152 / disableInstantCameraRow | DisableInstantCamera / DisableInstantCamera | media_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:153 / cameraInVideoMessages | CameraInVideoMessages / CameraInVideoMessages | media_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:162 / showSmallGifRow | ShowSmallGIF / ShowSmallGIF | stickers_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:163 / takeGIFasVideoRow | TakeGIFasVideo / TakeGIFasVideo | stickers_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:164 / autoPauseVideoRow | AutoPauseVideo / AutoPauseVideo | media_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:165 / disablePreviewVideoSoundShortcutRow | DisablePreviewVideoSoundShortcut / DisablePreviewVideoSoundShortcut | media_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:166 / dontAutoPlayNextVoiceRow | DontAutoPlayNextVoice / DontAutoPlayNextVoice | media_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:167 / showSpoilersDirectlyRow | showSpoilersDirectly / showSpoilersDirectly | media_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:172 / dontSendGreetingStickerRow | DontSendGreetingSticker / DontSendGreetingSticker | stickers_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:173 / hideGroupStickerRow | hideGroupSticker / hideGroupSticker | stickers_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:174 / maxRecentStickerCountRow | maxRecentStickerCount / maxRecentStickerCount | stickers_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:179 / transcribeProviderRow | TranscribeProvider / TranscribeProvider | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:187 / transcribeProviderCfCredentialsRow | CloudflareCredentials / CloudflareCredentials | messages_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:188 / transcribeProviderGeminiApiKeyRow | LlmProviderGeminiKey / LlmProviderGeminiKey | messages_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:189 / transcribeProviderOpenAiRow | TranscribeProviderOpenAI / TranscribeProviderOpenAI | messages_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:194 / chatMenuRow | ChannelAdministrators / ChannelAdministrators, EventLog, Statistics, ChannelPermissions, GroupMembers, ChatMenuItemBoostGroup, ChatMenuItemLinkedChat, ChatMenuItemToBeginning, ChatMenuItemGoToMessage, ChatMenuItemHideTitle, ChatMenuItemViewDeleted, ChatMenuItemClearDeleted, ChatMenuItemDeleteOwnMessages | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:211 / messageMenuRow | showAddToSavedMessages / showAddToSavedMessages, showRepeat, showDeleteDownloadedFile, showViewHistory, showTranslate, showShareMessages, showMessageHide, showReport, showAdminActions, showChangePermissions, showMessageDetails, Reactions, ReplyInPrivate, CopyLink, MessageMenuCopyFrame, CopyPhoto, CopyPhotoAsSticker, AddToStickers, AddToFavorites, NoQuoteForward, SetReminder, ShowAddToBookmark, RepeatAsCopy, TranslateMessageLLM | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:239 / mediaViewerMenuRow | MediaViewerMenuItemForward / MediaViewerMenuItemForward, MediaViewerMenuItemNoQuoteForward, MediaViewerMenuItemCopyFrame, MediaViewerMenuItemCopyPhoto, MediaViewerMenuItemSetProfilePhoto, MediaViewerMenuItemScanQRCode | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:249 / actionBarButtonRow | Reply / Reply, Edit, SelectBetween, Copy, Forward | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:258 / defaultDeleteMenuRow | DefaultDeleteMenu / DefaultDeleteMenu, DeleteBanUsers, DeleteReportSpam, DeleteAll, DoActionsInCommonGroups | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:268 / textStyleRow | TextStyle / TextStyle | messages_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:276 / groupedMessageMenuRow | GroupedMessageMenu / GroupedMessageMenu | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:277 / hideKeyboardOnChatScrollRow | HideKeyboardOnChatScroll / HideKeyboardOnChatScroll | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:278 / disableVibrationRow | DisableVibration / DisableVibration | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:279 / disableMarkdownRow | DisableMarkdown / DisableMarkdown | messages_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:280 / disableProximityEventsRow | DisableProximityEvents / DisableProximityEvents | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:281 / rememberAllBackMessagesRow | rememberAllBackMessages / rememberAllBackMessages | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:282 / typeMessageHintUseGroupNameRow | TypeMessageHintUseGroupName / TypeMessageHintUseGroupName | messages_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:283 / showSendAsUnderMessageHintRow | ShowSendAsUnderMessageHint / ShowSendAsUnderMessageHint | messages_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:284 / showQuickReplyInBotCommandsRow | ShowQuickReplyInBotCommands / ShowQuickReplyInBotCommands | messages_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:285 / hideBotButtonInInputFieldRow | HideBotButtonInInputField / HideBotButtonInInputField | messages_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:286 / hideReactionsRow | HideReactions / HideReactions | messages_extra | False | Source ownership; device pending |
| NekoChatSettingsActivity:291 / hideSendAsChannelRow | hideSendAsChannel / hideSendAsChannel | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:292 / hideShareButtonInChannelRow | HideShareButtonInChannel / HideShareButtonInChannel | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:293 / disableSwipeToNextRow | disableSwipeToNextChannel / disableSwipeToNextChannel, disableSwipeToNextTopic | navigation_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:302 / skipOpenLinkConfirmRow | SkipOpenLinkConfirm / SkipOpenLinkConfirm | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:303 / askBeforeCallRow | AskBeforeCalling / AskBeforeCalling | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:304 / repeatConfirmRow | repeatConfirm / repeatConfirm | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:305 / disableClickCommandToSendRow | DisableClickCommandToSend / DisableClickCommandToSend | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:306 / confirmAVRow | ConfirmAVMessage / ConfirmAVMessage | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:307 / confirmAllLinksRow | ConfirmAllLinks / ConfirmAllLinks | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:317 / searchHashtagDefaultPageChannelRow | SearchHashtagDefaultPageChannel / SearchHashtagDefaultPageChannel | messages_extra | True | Source ownership; device pending |
| NekoChatSettingsActivity:318 / searchHashtagDefaultPageChatRow | SearchHashtagDefaultPageChat / SearchHashtagDefaultPageChat | messages_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:104 / backAnimationStyleRow | BackAnimationStyle / BackAnimationStyle | navigation_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:114 / springAnimationCrossfadeRow | SpringAnimationCrossfade / SpringAnimationCrossfade | navigation_extra | False | Source ownership; device pending |
| NekoExperimentalSettingsActivity:115 / localPremiumRow | localPremium / localPremium | advanced_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:116 / unlimitedPinnedDialogsRow | UnlimitedPinnedDialogs / UnlimitedPinnedDialogs | advanced_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:117 / unlimitedFavedStickersRow | UnlimitedFavoredStickers / UnlimitedFavoredStickers | stickers_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:122 / boostUploadRow | uploadBoost / uploadBoost | advanced_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:127 / audioEnhanceRow | NoiseSuppressAndVoiceEnhance / NoiseSuppressAndVoiceEnhance | media_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:128 / sendMp4DocumentAsVideoRow | SendMp4DocumentAsVideo / SendMp4DocumentAsVideo | media_extra | False | Source ownership; device pending |
| NekoExperimentalSettingsActivity:129 / enhancedVideoBitrateRow | EnhancedVideoBitrate / EnhancedVideoBitrate | media_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:130 / customAudioBitrateRow | customGroupVoipAudioBitrate / customGroupVoipAudioBitrate | media_extra | False | Source ownership; device pending |
| NekoExperimentalSettingsActivity:131 / playerDecoderRow | VideoPlayerDecoder / VideoPlayerDecoder | media_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:140 / ghostModeRow | GhostMode / GhostMode | advanced_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:141 / regexFiltersEnabledRow | RegexFilters / RegexFilters | advanced_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:142 / saveLastSeenRow | SaveLocalLastSeen / SaveLocalLastSeen | advanced_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:143 / enableSaveDeletedMessagesRow | EnableSaveDeletedMessages / EnableSaveDeletedMessages | advanced_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:144 / enableSaveEditsHistoryRow | EnableSaveEditsHistory / EnableSaveEditsHistory | advanced_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:145 / messageSavingSaveMediaRow | MessageSavingSaveMedia / MessageSavingSaveMedia | advanced_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:146 / saveDeletedInPrivateChatsRow | SaveDeletedInPrivateChats / SaveDeletedInPrivateChats | advanced_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:147 / saveDeletedInGroupsRow | SaveDeletedInGroups / SaveDeletedInGroups | advanced_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:148 / saveDeletedInChannelsRow | SaveDeletedInChannels / SaveDeletedInChannels | advanced_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:149 / saveDeletedMessageForBotsUserRow | SaveDeletedMessageForBotUser / SaveDeletedMessageForBotUser | advanced_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:150 / saveDeletedMessageInBotChatRow | SaveDeletedMessageForBot / SaveDeletedMessageForBot | advanced_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:151 / replyToDeletedAsQuoteRow | ReplyToDeletedAsQuote / ReplyToDeletedAsQuote | advanced_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:152 / translucentDeletedMessagesRow | TranslucentDeletedMessages / TranslucentDeletedMessages | advanced_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:153 / useDeletedIconRow | UseDeletedIcon / UseDeletedIcon | advanced_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:154 / customDeletedMarkRow | CustomDeletedMark / CustomDeletedMark | advanced_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:155 / clearMessageDatabaseRow | ClearMessageDatabase / ClearMessageDatabase | advanced_extra | False | Source ownership; device pending |
| NekoExperimentalSettingsActivity:178 / showRPCErrorRow | ShowRPCError / ShowRPCError | advanced_extra | False | Source ownership; device pending |
| NekoExperimentalSettingsActivity:179 / forceFontWeightFallbackRow | forceFontWeightFallback / forceFontWeightFallback | appearance_extra | False | Source ownership; device pending |
| NekoExperimentalSettingsActivity:180 / disableChoosingStickerRow | disableChoosingSticker / disableChoosingSticker | stickers_extra | False | Source ownership; device pending |
| NekoExperimentalSettingsActivity:181 / disableFilteringRow | SensitiveDisableFiltering / SensitiveDisableFiltering | advanced_extra | False | Source ownership; device pending |
| NekoExperimentalSettingsActivity:182 / devicePerformanceClassRow | PerformanceClass / PerformanceClass | advanced_extra | False | Source ownership; device pending |
| NekoExperimentalSettingsActivity:192 / disableStoriesRow | DisableStories / DisableStories | advanced_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:193 / hideFromHeaderRow | HideStoriesFromHeader / HideStoriesFromHeader | advanced_extra | True | Source ownership; device pending |
| NekoExperimentalSettingsActivity:198 / enablePanguOnSendingRow | EnablePanguOnSending / EnablePanguOnSending | advanced_extra | False | Source ownership; device pending |

## Delegated editors

Bubbles, Header, Composer, BottomTabs, AppNavigation, BubbleInteraction, Plugins, AI, PillStack, Emoji, IconPacks, MessageAnimations, Cloud and Passcode remain their original classes. Their settings logic is not copied or rewritten. Their complete device interaction and nested preference audit remains an integration acceptance gate. Original Telegram account, privacy, storage, download, language, and chat settings remain native; only additional legacy duplicate entry points are gated in the Connected client.
