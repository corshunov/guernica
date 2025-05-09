#!/bin/sh

cd "/home/tami/videos"

mpv \
    "sun_clean_overlay.mp4" \
    --loop-file=inf \
    --aid=no \
    --drm-draw-plane=overlay \
    --drm-drmprime-video-plane=primary \
    --vf='@over:lavfi="movie=SUN-eyeball-FHD.png[eyeball]; movie=SUN-eyelead-Half-open-FHD.png[halflids]; movie=SUN-eyelead-full-closed-FHD.png[fulllids]; [vid1][eyeball]overlay@eye=x=800:y=390[witheye]; [witheye][halflids]overlay@halflids=x=404:y=340[withhalf]; [withhalf][fulllids]overlay@fulllids=x=404:y=340[vo]"' \
    --input-ipc-server=/tmp/mpvsocket \
    --osd-level=0 \
    #-v \

    #--vo=drm \
    #--hwdec=v4l2m2m \
    #--audio-device=alsa/hdmi:CARD=vc4hdmi \
    #--idle=yes \
    #--keep-open=always \
