#!/bin/sh

mpv \
    "video.mp4" \
    --loop-file=inf \
    --aid=no \
    --vo=drm \
    --hwdec=v4l2m2m \
    --drm-draw-plane=overlay \
    --drm-drmprime-video-plane=primary \
    --input-ipc-server=/tmp/mpvsocket \
    --osd-level=0 \
    #-v
