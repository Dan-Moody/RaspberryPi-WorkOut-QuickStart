#!/bin/bash

# 1. Close heavy apps (keep your Flask server alive!)
pkill -f chromium || true
sleep 0.5

# 2. Export Wayland/X11 display variables for labwc on Raspberry Pi OS
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export WAYLAND_DISPLAY=wayland-0
export DISPLAY=:0

# 3. Launch scrcpy tuned for Pi 3 v1.2 (USB or already-connected ADB over TCP/IP)
scrcpy \
  --fullscreen \
  --max-size 1024 \
  --video-bit-rate 2M \
  --max-fps 30 \
  --no-audio \
  --stay-awake \
  --turn-screen-off
