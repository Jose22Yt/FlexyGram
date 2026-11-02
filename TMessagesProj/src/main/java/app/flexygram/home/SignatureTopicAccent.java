/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

/** Native forum highlight overlay: approximately 10% light / 14% dark. */
public final class SignatureTopicAccent {
    private SignatureTopicAccent() {}
    public static int overlay(int accent, boolean dark) {
        return (accent & 0x00ffffff) | ((dark ? 36 : 26) << 24);
    }
}
