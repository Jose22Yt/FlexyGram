# Canonical placement and preservation

No application setting store, key or value is copied, renamed or reset. Bundle keys describe temporary screen/scroll state only. The existing ConfigItem/NaConfig/NekoConfig/AppearanceConfig/ChatsConfig/LiquidNavigationConfig, Signature config objects and FlexyFiles getters/setters remain authoritative.

| Canonical category | Old editors / source | New presentation | Preservation and validation |
| --- | --- | --- | --- |
| Chat | HeaderSettingsActivity | First preview and original controls | Click handler identical; local holder position translated |
| Chat | BubbleSettingsActivity | Second preview and original conditional rows/sliders | Config/render/blur engines unchanged; click handler identical |
| Chat | FlexyComposerSettingsActivity | Third preview before style/geometry controls | Original setters/click logic; preview row moved before style row |
| Chat | OpenExteraChats messages, menus, media, stickers; residual NekoChat/General/Experimental | Original rows directly concatenated by ownership | Original callbacks reused; existing reset action surfaced as row; no new preference |
| Chat | BubbleInteraction / existing delete selector | Native controls inline; existing selector remains a dialog | Original controller logic reused, no intermediate message-animation page |
| Home | OpenExteraAppearance layout/avatars/folders; chat smart previews/hiding; residual appearance controls | One list using original previews/widgets | Global Signature rendering and Telegram folder management unchanged |
| Universal | OpenExteraGeneral general/profile/archive; appearance fonts/effects; Other; residual general/advanced; launcher selector | Direct controls in one list | Original account-side effects and deferred/restart conditions preserved; styles and config stores unchanged |
| AyuMoments | GhostModeActivity + OpenExteraAyuMomentsActivity | Both original row adapters inline | Old ghost navigation row omitted only while embedded; duplicate ClearMessageDatabase extra omitted because native Ayu DB maintenance owns it |
| Plugins | Plugins, AI, advanced translation, PillStack | Existing specialized managers; original translation presentation controls inline | No plugin/Python backend changes, no new settings engine |
| FlexyFiles | Former Studio/Files opt-in and help | Separate direct page | Original `flexyfiles_local` / `enabled` getter/setter; no new format support or backend |
| Files and downloads | Original General save path / per-chat subfolders | Storage controls only | Original chooser/handlers; FlexyFiles module controls are not repeated here |
| Navigation and gestures | BottomTabs; original AppNavigation simple controls; Chats gesture rows; residual navigation controls | Controls directly accessible | Original four navigation callbacks moved once into shared handler; predictive slider uses original UtilsConfig |
| Navigation and gestures | AppNavigation drag/reorder menu | Specialized reorder editor only | `menuOnly` hides the simple controls already on the parent page; original reorder algorithm preserved |
| FlexyStudio | Existing export/import/share operations | Exactly three operations, monochrome navigation glyphs | Existing transport/validation logic unchanged |
| FlexyGram information | Existing About/legal texts | Version + legal/source information and Remix attribution | Original legal credits retained; actual BuildVars version, full icon license bundled in assets |

`inventory.json` contains the 213 named legacy rows (including headers/navigation aliases), 161 legacy ConfigCells and native controller row declarations. It records identifiers/source expressions, not secret values. Aliases are not necessarily preference keys; conditional source declarations do not demonstrate physical visibility/persistence. The original detailed source inventory remains in `docs/settings2/SETTINGS_INVENTORY.md`.

## Duplicate prevention and compatible links

- The root exclusively renders Settings3Registry's ten entries. Old registry metadata exists only for legacy source ownership/search IDs.
- Original Telegram settings remain native; the existing Settings2 removals of duplicate extra entry points remain in the base.
- Each scoped legacy row keeps its owner and anonymous dependent rows. Multi-owner scopes are unions within one controller rather than cloning controls.
- Search results resolve to direct categories; confirmed old value-import handling delegates to the original ConfigItem import path. Numeric historical row positions and aliases must be tested against real expanded/conditional states; no broad compatibility claim is made from static routing.
- Native row long-press sharing is forwarded with local row keys instead of the outer/global position.
- Specialized managers retained for complex workflows must receive a final runtime duplicate audit; this inventory is not proof that every backend has only one possible access path.

## Integration and rollback

1. Stack this draft on PR161's source branch; do not restore older PR141 files or merge main/develop automatically.
2. Review controller composition, source/account/theme/lifecycle initialization, notification offsets, late callbacks and activity-result handling first. These are the principal new risks.
3. Run the validation commands and an actual approved full Beta build. Existing protected source/signing checks remain mandatory.
4. Capture actual Chat/Home/Universal/navigation screens and verify every affected option and stored value on the Poco X8 Pro. No physical acceptance is claimed here.
5. Integrate PR158 FlexyFiles separately when approved; this branch does not modify its backend, archive/preview logic, RecyclerListView or DialogsActivity.
6. If regression occurs, revert the feature commit. No preference migration needs reversing. Coordinate any later changes made on top of this feature before reverting shared base classes.
