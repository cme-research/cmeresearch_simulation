#!/bin/bash
set -e

# Source ROS 2 and the built workspace
source /opt/ros/jazzy/setup.bash
source /ros2_ws/install/setup.bash

# ── Display handling ───────────────────────────────────────────────────────────
# If DISPLAY is not set (headless / CI), start a virtual framebuffer so that
# Webots can initialise its OpenGL context.
if [ -z "${DISPLAY}" ]; then
    echo "[entrypoint] No DISPLAY found – starting Xvfb on :99"
    Xvfb :99 -screen 0 1280x1024x24 &
    export DISPLAY=:99
    sleep 1
fi

exec "$@"
