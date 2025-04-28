#!/bin/sh

mpv \
    "/home/tami/videos/test.mp4" \
    --loop-file=inf \
    --vo=gpu \
    --hwdec=v4l2m2m-copy \
    --drm-draw-plane=overlay \
    --drm-drmprime-video-plane=primary \
    --input-ipc-server=/tmp/mpvsocket \
    --idle=yes \
    --keep-open=always \
    -v \
    # --osc=no \
    #--audio-device=alsa/hdmi:CARD=vc4hdmi \
