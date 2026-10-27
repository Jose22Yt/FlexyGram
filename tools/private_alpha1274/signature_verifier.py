"""Alpha1275 packaged launcher policy; all other original APK checks stay unchanged."""
import verify_apk as original

def has_signature_launcher(xmltree):
    """Require one exported MAIN/LAUNCHER alias, the approved blue default."""
    def enabled(node):
        return node['attrs'].get('enabled', 'true') not in ('false', '(type 0x12)0x0', '0x0')
    launchers = []
    for app in original.application_nodes(xmltree):
        if not enabled(app):
            continue
        activities = set()
        for node in app['children']:
            if node['tag'] == 'activity':
                if enabled(node):
                    activities.add(node['attrs'].get('name'))
            if node['tag'] not in ('activity', 'activity-alias') or not enabled(node):
                continue
            for intent in node['children']:
                if intent['tag'] != 'intent-filter':
                    continue
                actions = {c['attrs'].get('name') for c in intent['children'] if c['tag'] == 'action'}
                categories = {c['attrs'].get('name') for c in intent['children'] if c['tag'] == 'category'}
                if 'android.intent.action.MAIN' in actions and 'android.intent.category.LAUNCHER' in categories:
                    launchers.append((node, set(activities)))
                    break
    if len(launchers) != 1:
        return False
    node, activities = launchers[0]
    attrs = node['attrs']
    return (node['tag'] == 'activity-alias'
            and attrs.get('name') == 'org.telegram.messenger.FlexyBlueIcon'
            and attrs.get('targetActivity') in activities
            and attrs.get('exported') in ('true', '(type 0x12)0xffffffff'))

if __name__ == '__main__':
    original.has_launcher_alias = has_signature_launcher
    original.main()
