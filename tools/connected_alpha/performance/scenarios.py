"""Only manually prepared test workloads. Never inspect or operate owner conversations."""
SCENARIOS = {
    'cold_start': 'Process cold; am force-stop/start only after explicit test-device approval.',
    'warm_start': 'Warm existing process/activity; no force-stop or data clear.',
    'chat_open': 'Open the same nonprivate test conversation.',
    'chat_close': 'Return from that test conversation.',
    'chat_repeat': 'Repeat identical open/close cycles; include rapid/interrupted Back.',
    'dialogs_scroll': 'Scroll the same long synthetic/test chat list.',
    'messages_scroll': 'Scroll the same fixed test-message corpus.',
    'folders': 'Switch the same folders/tabs in the same order.',
    'keyboard': 'Open/close the keyboard in an empty test composer.',
    'settings': 'Open/close the same settings page.',
    'send_test_message': 'Operator sends only a synthetic message to a test account.',
    'reactions': 'Operator opens reactions on a synthetic test message.',
    'player_open_close': 'Open/close the same music track/queue state.',
    'music_navigation': 'Repeat navigation with the same licensed local test music.',
    'theme_change': 'Apply the same theme changes, record sequence in workload ID.',
    'background_resume': 'Resume after the same controlled background interval.',
    'preview_release': 'Work1 P0 observation only: release/back while preview closes; do not claim fixed.',
    'configuration': 'Same orientation/font/window changes on the test device.',
    'memory_pressure': 'Operator-controlled test pressure; no system memory settings changed.',
    'refresh_change': 'Observe operator-selected display changes; never change device settings.',
}

# Performance3 extends the same operator-driven lab; no generated touch events.
SCENARIOS.update({
    'multitap': 'Operator performs fixed rapid test-chat taps/Back interruptions; never owner conversations.',
    'image_messages': 'Scroll an equivalent synthetic image corpus, with matched thumbnail/cache state.',
    'stickers': 'Scroll the same licensed test sticker/emoji corpus and reaction state.',
    'typing': 'Operator types/sends synthetic test text; separate keyboard timing from layout/frame duration.',
    'player_idle': 'Same test workload with playback stopped and no pending player transition.',
    'glass_on': 'Same approved Glass style enabled; record exact theme/wallpaper/cache state.',
    'glass_off': 'Same workload with Glass disabled by operator; do not change global device settings.',
})
