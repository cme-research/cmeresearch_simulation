# ──────────────────────────────────────────────────────────────────────────────
# CMEXAIII Webots Simulation Image
#
# Builds a self-contained ROS 2 Jazzy + Webots R2025a image for the CMEXAIII
# mecanum robot simulation including SLAM Toolbox and Nav2.
#
# Build (from the workspace root ros2_ws/):
#   docker build -f src/cmeresearch_simulation/docker/Dockerfile \
#                -t cmeresearch/simulation:latest .
#
# Run with GUI (X11 forwarding):
#   xhost +local:docker
#   docker run -it --rm \
#     -e DISPLAY=$DISPLAY \
#     -v /tmp/.X11-unix:/tmp/.X11-unix \
#     cmeresearch/simulation:latest \
#     ros2 launch cmeresearch_simulation cmexaiii_webots_full.launch.py
#
# Run headless (Xvfb virtual framebuffer, gui:=false):
#   docker run -it --rm \
#     cmeresearch/simulation:latest \
#     ros2 launch cmeresearch_simulation cmexaiii_webots_full.launch.py gui:=false
# ──────────────────────────────────────────────────────────────────────────────

FROM ros:jazzy-ros-base AS base

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-c"]

# ── System packages ────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build tools
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    python3-pip \
    # ROS utilities
    ros-jazzy-xacro \
    ros-jazzy-robot-state-publisher \
    ros-jazzy-joint-state-broadcaster \
    ros-jazzy-ros2-controllers \
    ros-jazzy-controller-manager \
    ros-jazzy-mecanum-drive-controller \
    # webots_ros2
    ros-jazzy-webots-ros2-driver \
    ros-jazzy-webots-ros2-control \
    # Navigation & SLAM
    ros-jazzy-nav2-bringup \
    ros-jazzy-slam-toolbox \
    ros-jazzy-twist-mux \
    # Display (Xvfb for headless mode)
    xvfb \
    x11-xserver-utils \
    # Misc
    wget \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# ── Webots R2025a ──────────────────────────────────────────────────────────────
RUN wget -qO /etc/apt/trusted.gpg.d/Cyberbotics.asc \
      https://cyberbotics.com/Cyberbotics.asc \
 && echo "deb https://cyberbotics.com/debian/ binary-amd64/" \
      > /etc/apt/sources.list.d/Cyberbotics.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends webots \
 && rm -rf /var/lib/apt/lists/*

# ── Workspace ──────────────────────────────────────────────────────────────────
WORKDIR /ros2_ws

# Clone additional source dependencies via vcstool.
# cmeresearch_simulation itself is copied from the build context below.
COPY src/cmeresearch_simulation/docker/simulation.repos /tmp/simulation.repos
RUN mkdir -p src \
 && vcs import src < /tmp/simulation.repos

# Copy this package's source into the workspace
COPY src/cmeresearch_simulation src/cmeresearch_simulation

# ── ROS dependencies ───────────────────────────────────────────────────────────
RUN source /opt/ros/jazzy/setup.bash \
 && rosdep update \
 && rosdep install \
      --from-paths src \
      --ignore-src \
      --rosdistro jazzy \
      -y \
      --skip-keys "webots_ros2_driver webots_ros2_control"

# ── Build ──────────────────────────────────────────────────────────────────────
RUN source /opt/ros/jazzy/setup.bash \
 && colcon build \
      --cmake-args -DCMAKE_BUILD_TYPE=Release \
      --executor parallel \
      --event-handlers console_cohesion+

# ── Runtime stage ──────────────────────────────────────────────────────────────
FROM base AS runtime

# Entrypoint handles display setup (Xvfb if DISPLAY unset) and sources the workspace
COPY src/cmeresearch_simulation/docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Webots stores its cache in the user's home; make it writable
ENV WEBOTS_HOME=/usr/local/webots
ENV HOME=/root

ENTRYPOINT ["/entrypoint.sh"]
CMD ["ros2", "launch", "cmeresearch_simulation", "cmexaiii_webots_full.launch.py"]
