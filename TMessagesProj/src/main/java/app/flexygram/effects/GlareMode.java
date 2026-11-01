/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.effects;

/** Cherrygram's public order, adapted to FlexyGram's existing persisted enum. No new store. */
public final class GlareMode {
    public static final int DISABLED=0,DEFAULT=1,SOLID=2;
    private GlareMode(){}
    /** Existing storage: GLARE=0, SOLID=1, HIDDEN=2. Never reinterpret saved values. */
    public static int fromStored(int stored){switch(stored){case 2:return DISABLED;case 1:return SOLID;default:return DEFAULT;}}
    public static int toStored(int choice){switch(choice){case DISABLED:return 2;case DEFAULT:return 0;case SOLID:return 1;default:throw new IllegalArgumentException("Unknown glare mode");}}
}
