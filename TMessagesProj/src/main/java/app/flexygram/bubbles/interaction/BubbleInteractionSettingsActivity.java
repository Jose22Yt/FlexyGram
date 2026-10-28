/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import app.flexygram.motion.FlexyMotionActivity;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Cells.TextInfoPrivacyCell;

/** Chats → Burbujas → Interacción de mensajes, using native Signature Matte rows. */
public final class BubbleInteractionSettingsActivity extends SignatureMatteSettingsActivity {
    private int titleRow, tapRow, panelRow, stickerRow, physicsRow, infoRow;
    @Override protected String getActionBarTitle() { return "Interacción de mensajes"; }
    @Override protected void updateRows() {
        super.updateRows();
        titleRow = addRow();
        tapRow = addRow("flexyBubbleTapMotion");
        panelRow = addRow("flexyBubbleContextPanel");
        stickerRow = addRow("flexyBubbleRealSticker");
        physicsRow = addRow("flexyBubbleMotionPhysics");
        infoRow = addRow();
    }
    @Override protected BaseListAdapter createAdapter(Context context) { return new Adapter(context); }
    @Override protected void onItemClick(View view, int position, float x, float y) {
        Context context = getParentActivity();
        if (context == null) return;
        if (position == tapRow) BubbleInteractionSettings.setTapMotion(
                context, !BubbleInteractionSettings.tapMotion(context));
        else if (position == panelRow) BubbleInteractionSettings.setSignaturePanel(
                context, !BubbleInteractionSettings.signaturePanel(context));
        else if (position == stickerRow) BubbleInteractionSettings.setStickerConversion(
                context, !BubbleInteractionSettings.stickerConversion(context));
        else if (position == physicsRow) { presentFragment(new FlexyMotionActivity()); return; }
        else return;
        listAdapter.notifyItemChanged(position);
    }
    private final class Adapter extends MatteListAdapter {
        Adapter(Context context) { super(context); }
        @Override public int getItemViewType(int position) {
            if (position == titleRow) return TYPE_HEADER;
            if (position == infoRow) return TYPE_INFO_PRIVACY;
            if (position == physicsRow) return TYPE_SETTINGS;
            return TYPE_CHECK;
        }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder, int position, boolean partial) {
            Context c = holder.itemView.getContext();
            if (position == titleRow)
                ((tw.nekomimi.nekogram.ui.cells.HeaderCell)holder.itemView).setText("BURBUJAS Y MOVIMIENTO");
            else if (position == tapRow)
                ((TextCheckCell)holder.itemView).setTextAndCheck("Rebote al tocar un mensaje", BubbleInteractionSettings.tapMotion(c), false);
            else if (position == panelRow)
                ((TextCheckCell)holder.itemView).setTextAndCheck("Panel de acciones FlexyGram (experimental)", BubbleInteractionSettings.signaturePanel(c), false);
            else if (position == stickerRow)
                ((TextCheckCell)holder.itemView).setTextAndCheck("Convertir burbuja en sticker (experimental)", BubbleInteractionSettings.stickerConversion(c), false);
            else if (position == physicsRow)
                ((TextSettingsCell)holder.itemView).setTextAndValue("Velocidad y amortiguación", "Flexy Motion Engine", true);
            else if (position == infoRow)
                ((TextInfoPrivacyCell)holder.itemView).setText("El toque no debe interferir con enlaces, scroll o selección. La conversión requiere un mensaje elegible y confirmar el envío; no se habilita el envío automático.");
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder) {
            int p = holder.getAdapterPosition();
            return p == tapRow || p == panelRow || p == stickerRow || p == physicsRow;
        }
    }
}
