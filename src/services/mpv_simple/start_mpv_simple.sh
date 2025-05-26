#!/bin/sh

cd /home/tami/guernica/conf/media

mpv \
    "video.mp4" \
    --loop-file=inf \
    --aid=no \
    --vo=gpu \
    --hwdec=v4l2m2m \
    --drm-draw-plane=overlay \
    --drm-drmprime-video-plane=primary \
    --input-ipc-server=/tmp/mpvsocket \
    --osd-level=0 \
    #-v
