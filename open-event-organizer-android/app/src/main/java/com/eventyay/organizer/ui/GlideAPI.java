package com.eventyay.organizer.ui;

import android.content.Context;
import android.net.TrafficStats;

import com.bumptech.glide.Glide;
import com.bumptech.glide.GlideBuilder;
import com.bumptech.glide.Registry;
import com.bumptech.glide.annotation.GlideModule;
import com.bumptech.glide.integration.okhttp3.OkHttpUrlLoader;
import com.bumptech.glide.load.engine.cache.InternalCacheDiskCacheFactory;
import com.bumptech.glide.load.model.GlideUrl;
import com.bumptech.glide.module.AppGlideModule;

import java.io.InputStream;

import okhttp3.OkHttpClient;

@GlideModule
public final class GlideAPI extends AppGlideModule {

    @Override
    public void registerComponents(Context context, Glide glide, Registry registry) {
        OkHttpClient client = new OkHttpClient.Builder()
            .addInterceptor(chain -> {
                TrafficStats.setThreadStatsTag(0xF00D);
                try {
                    return chain.proceed(chain.request());
                } finally {
                    TrafficStats.clearThreadStatsTag();
                }
            })
            .build();
        registry.replace(GlideUrl.class, InputStream.class, new OkHttpUrlLoader.Factory(client));
    }

    // TODO: Modify the options here according to the need
    @Override
    public void applyOptions(Context context, GlideBuilder builder) {
        int diskCacheSizeBytes = 1024 * 1024 * 10; // 10mb
        builder.setDiskCache(new InternalCacheDiskCacheFactory(context, diskCacheSizeBytes));
    }

    @Override
    public boolean isManifestParsingEnabled() {
        return false;
    }
}
