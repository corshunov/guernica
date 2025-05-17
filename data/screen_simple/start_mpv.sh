#!/bin/sh

mpv \
    "video.mp4" \
    --loop-file=inf \
    --aid=no \
    --drm-draw-plane=overlay \
    --drm-drmprime-video-plane=primary \
    --vf='@over:lavfi="movie=SUN-eyeball-FHD.png[eyeball]; movie=SUN-eyelead-Half-open-FHD.png[halflids]; movie=SUN-eyelead-full-closed-FHD.png[fulllids]; [vid1][eyeball]overlay@eye=x=800:y=390[witheye]; [witheye][halflids]overlay@halflids=x=-2000:y=340[withhalf]; [withhalf][fulllids]overlay@fulllids=x=-2000:y=340[vo]"' \
    --input-ipc-server=/tmp/mpvsocket \
    --osd-level=0 \
    #-v
