#!/bin/sh

mpv \
    "/home/tami/videos/head_on_floor_1920x1080.mp4" \
    --loop-file=inf \
    --aid=no \
    --vo=gpu \
    --hwdec=v4l2m2m \
    --drm-draw-plane=overlay \
    --drm-drmprime-video-plane=primary \
    --input-ipc-server=/tmp/mpvsocket \
    --osd-level=0 \
    -v \

    #--audio-device=alsa/hdmi:CARD=vc4hdmi \
    #--idle=yes \
    #--keep-open=always \
