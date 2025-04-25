#!/bin/sh

mpv \
    --vo=gpu \
    --hwdec=v4l2m2m \
    --drm-draw-plane=overlay \
    --drm-drmprime-video-plane=primary \
    --audio-device=alsa/hdmi:CARD=vc4hdmi \
    --input-ipc-server=/tmp/mpvsocket \
    --idle=yes \
    --keep-open=always \
    -v \
    # --osc=no \
