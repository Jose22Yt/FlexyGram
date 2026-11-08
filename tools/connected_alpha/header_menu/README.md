# Header menu investigation

```sh
python tools/connected_alpha/header_menu/run.py --sdk-root "$ANDROID_HOME" --instrument-motion
```

Requires Maven and JDK 17+. No APK or account is initialized.

The probe copies the production `ActionBarPopupWindow`, `PopupSwipeBackLayout`
and `LayoutHelper` classes, plus the menu controller's `createPopupLayout`,
`toggleSubMenu`, `hasSubMenu` and `updateOrShowPopup` methods. The contents
factory, account services, theme/blur provider and host bar are explicit fixtures.
Rows are real Android TextViews; the test verifies measured dimensions and drawn
text pixels for native/custom anchors and plain/blur surfaces, including system
animation scale zero. It does not exercise the complete chat's touch hierarchy.

`--instrument-motion` additionally applies the production `FastMotionVisitor` to
the compiled popup/controller classes and repeats the Android tests using the
production `FastMotion` runtime. Spring services are unused test doubles.

Observed result against beta.19: both tests pass, before and after instrumentation.
This does **not** identify or fix the reported device failure. The next required
evidence is whether opening overflow creates a modal/invisible window or leaves
chat scrolling immediately available. The supplied device video exceeded the
attachment transfer limit of 32 MiB and could not be inspected.
