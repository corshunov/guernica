#!/bin/sh

mpv \
    "/home/tami/videos/video.mp4" \
    --loop-file=inf \
    --audio-device=alsa/hdmi:CARD=vc4hdmi \
    --vo=gpu \
    --hwdec=v4l2m2m \
    --drm-draw-plane=overlay \
    --drm-drmprime-video-plane=primary \
    --input-ipc-server=/tmp/mpvsocket \
    --osc=no \
    --idle=yes \
    --keep-open=always \
    -v \
