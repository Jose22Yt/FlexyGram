/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.motion;

/** Explicit opt-in for views that draw their own pressure; avoids concurrent native scale animators. */
public interface FlexyPressOwner {
    void setFlexyPressEnabled(boolean enabled);
}
