# FlexyGram — Flexy Liquid Navigation (Work 1 handoff)

## Approved user experience
Reference video `50444(1).mp4`: iOS-like floating bottom tab bar with an indicator that follows the finger immediately, stretches *subtly* during horizontal motion and settles softly into the chosen tab. Dynamic tabs and a settings preview in **Apariencia → Barra inferior / Flexy Liquid Navigation**.

This branch starts from **PR #123**, SHA `e00b33e806921017ad74ff50eb5ec88607131d9c`. It is independent from #124 popup, #125 bubble Glass, #126 header/composer native Glass. No merge, signed APK or hardware test has been performed by this branch creator.

## Code already implemented
- `MainTabsLayout` now has an **opt-in direct horizontal-drag route** for the existing iOS-style tab bar. Starts after native touch slop (not the old long-press delay), tracks the finger without repeated navigation operations, and commits a single `target.performClick()` on release. Supports cancel and safe snapping with one damped `SpringAnimation`. The original native long-press helper remains when the feature is disabled. Existing tabs' own native long-click listeners are not removed.
- The transparent, theme-colored selector uses the existing main tabs Glass background. `LiquidNavigationMath` bounds stretch to 19% of indicator width at maximum elasticity, and applies a small shape compression. The live selector uses one Paint and RectF; no bitmap, shaders, overdraw layer or reflection is created. This is a *translucent* indicator over the native glass, NOT an additional blurred, physics-simulated refractive lens.
- `LiquidNavigationConfig` persists master toggle (OFF by default, no regression for existing users), elasticity (default 65%) and opacity (default 55%) in local app prefs.
- New `LiquidNavigationSettingsActivity` wired from **Apariencia → Navegación**. Offers real controls for native tab slots: Contacts visible, Profile visible, Calls instead of Settings, Feed instead of Contacts. It preserves **Chats** and Settings/Calls slot so the root never becomes inaccessible. Calls and Feed update through existing NotificationCenter events. Existing `MainTabsHelper`, `NaConfig`, account calls setting and `AppearanceConfig` remain the single sources of truth.
- `LiquidNavigationPreviewView` uses real tab-visibility flags to update instantly, lays out 2–4 native-compatible slots, and responds to horizontal finger movement without affecting actual chats.
- English/Spanish/Russian strings. Scope limited to existing MainTabsActivity and MainTabsLayout. Source wiring and pure-math regression contracts included in `.github/workflows/flexy-liquid-navigation-contract.yml`.

## Important: functionality NOT implemented / do not misrepresent
- **New Groups/Channels/Saved separate permanent root tabs and arbitrary reordering are not yet implemented.** MainTabsActivity currently has four fragment positions, with Contacts/Feed and Calls/Settings sharing slots. Visually adding imaginary fifth/sixth buttons without proper `ViewPagerFixed` routing would open wrong fragments. Work 1 must design a safe route adapter (or shortcuts that explicitly open the corresponding folders/screens), update fragment state and save ordering atomically, maintain scroll navigation alignment, screen readers, account switching and restore on process death.
- The settings preview is interactive for touch and count, but it does **not** use the native blur3 refractive renderer because it does not have the live wallpaper source.
- Existing native iOS style is a prerequisite for the live gesture. Style OFF, master toggle OFF, accessibility and other navigation modes retain native behavior.
- Runtime visibility of toggles for Contacts/Profile from within Appearance may need a MainTabsActivity rebuild after returning from the settings fragment. Calls/Feed use native event notifications. Do not force an unsafe rebuild mid-navigation.
- No proof of exactly matching proprietary iOS 27 liquid physics, 120/144Hz FPS, performance or APK build is claimed.

## Work 1 next engineering
1. Run full Android Gradle build and test the new `onInterceptTouchEvent()` interaction with nested main tabs: horizontal drag immediately without waiting for long press; vertical gesture passed through; single click on UP; cancel/multi-pointer/detach; restored selection if target navigation is rejected. Do not allow duplicate clicks or trigger clicks while dragging.
2. Validate that the custom indicator's translucent fill stays visible over native `blur3` surface ON/OFF. Verify outline contrast in light/dark and low battery, animated wallpapers; no new blur engine. Verify the default "OFF" path remains identical.
3. Confirm Native `MainTabsHelper` contact/profile hide rebuild and feed/calls native events, account switches and settings persistence. At least 2 functional tabs always available. Match `ViewPagerFixed` fragment mapping.
4. Implement fully routed extra categories (Groups/Channels/Saved) and reorder only once actual destinations, tab order, fragments, pager order and accessibility have a proven mapping. Avoid fake toggles or hardcoded placeholders. Add screen reader and keyboard/directional navigation.
5. Refine stretch with spring damping and velocity if device comparison to user video shows visual discrepancies; avoid overshoot, unstable spring or chasing finger with delayed bounds.
6. Device acceptance: Poco X8 Pro, Android 17, HyperOS 4. Rapid touches, continuous drag both ways, custom folders, RTL, keyboard, predictive back, dark/light, native Liquid Glass, profile, notifications, long press, 60/120/144Hz. No crashes or freeze.
7. Do not merge this work or send users a compiled APK unless Gradle/source validation, integration review and signed private build pass.

## Code ownership / privacy
Settings only store appearance preferences. No chat content, media or Telegram account identifiers are serialized by the Liquid indicator. No gestures are recorded or uploaded. Preview is synthetic and does not read messages.
