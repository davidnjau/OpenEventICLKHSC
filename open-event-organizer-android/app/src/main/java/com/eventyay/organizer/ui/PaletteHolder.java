package com.eventyay.organizer.ui;

import android.view.ViewGroup;
import android.widget.TextView;

// TODO: Reimplement once Glide Palette is fixed
public final class PaletteHolder {

    private static PaletteHolder paletteHolderInstance;

    private PaletteHolder() {
        // Never Called
    }

    public static PaletteHolder getInstance() {
        synchronized (PaletteHolder.class) {
            if (paletteHolderInstance == null)
                paletteHolderInstance = new PaletteHolder();
            return paletteHolderInstance;
        }
    }

    public void registerHeader(String key, ViewGroup viewGroup) {
        // No-op: GlidePalette removed
    }

    public void registerText(String key, TextView textView) {
        // No-op: GlidePalette removed
    }
}
