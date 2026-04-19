# CME Research Simulation Package

Simulation environments for CME Research autonomous mobile robots.
Currently supports **Webots** (primary, ROS 2 Jazzy) and Stage (legacy, ROS 1).

## Contents

| Directory | Description |
|---|---|
| `worlds/cmexaiii/webots/` | Webots world file for CMEXAIII |
| `worlds/cmexaiii/` | Stage world for CMEXAIII (legacy) |
| `worlds/cmexa/` | Stage worlds for CMEXA (legacy) |
| `worlds/cmexamini/` | Early Webots prototype files |
| `config/cmexaiii/` | ros2\_control controller configuration |
| `resource/` | Webots driver URDF (hardware plugin config) |
| `launch/` | Launch files |
| `maps/` | Pre-built occupancy grid maps (house, laboriii) |
| `scripts/` | Utility scripts (Stage odometry bridge) |

---

## Webots Simulation – CMEXAIII

The CMEXAIII is a 4-wheeled mecanum-drive (omnidirectional) robot.
The Webots simulation uses **webots\_ros2\_control** to expose the four wheel
joints via **ros2\_control**, driven by **mecanum\_drive\_controller**.
Both LiDAR sensors publish on the same topics as the real hardware, so the
full navigation and SLAM stack works without modification.

### Prerequisites

**1. Webots R2025a**

```bash
# Download the .deb from https://cyberbotics.com or install via apt:
sudo apt install webots
```

Verify the installed version:

```bash
webots --version   # must report R2025a
```

**2. ROS 2 Jazzy workspace** with the following packages checked out under `src/`:

| Package | Repository |
|---|---|
| `cmeresearch_simulation` | this repo |
| `cmeresearch_description` | cme-research/cmeresearch\_description |
| `cmeresearch_msgs` | cme-research/cmeresearch\_msgs |

**3. webots\_ros2 ROS packages**

```bash
sudo apt install ros-jazzy-webots-ros2-driver \
                 ros-jazzy-webots-ros2-control
```

**4. ros2\_controllers** (provides `mecanum_drive_controller`)

```bash
sudo apt install ros-jazzy-ros2-controllers
```

**5. Build the workspace**

```bash
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -y
colcon build --packages-select cmeresearch_msgs cmeresearch_description cmeresearch_simulation
source install/setup.bash
```

---

### Running the simulation

```bash
ros2 launch cmeresearch_simulation cmexaiii_webots.launch.py
```

**Launch arguments**

| Argument | Default | Description |
|---|---|---|
| `gui` | `true` | Open the Webots 3D window |
| `use_sim_time` | `true` | Use Webots simulation clock |
| `rviz` | `false` | Launch RViz2 alongside Webots |

Example – headless (no GUI, useful for CI or remote machines):

```bash
ros2 launch cmeresearch_simulation cmexaiii_webots.launch.py gui:=false
```

Example – with RViz:

```bash
ros2 launch cmeresearch_simulation cmexaiii_webots.launch.py rviz:=true
```

> **X11 / display note:** Webots requires a display even in headless mode
> unless you use a virtual framebuffer.  On a remote machine run:
> ```bash
> export DISPLAY=:0   # or use Xvfb
> ```

---

### What the launch file starts

```
WebotsLauncher  ──────────────────────────────  opens indoor_office.wbt
Ros2Supervisor  ──────────────────────────────  Webots ↔ ROS 2 time bridge
robot_state_publisher  ───────────────────────  full URDF from cmeresearch_description
WebotsController (cmexaiii)  ─────────────────  webots_ros2_driver + controller_manager
  └─ webots_ros2_control::Ros2Control  ──────── reads wheel RotationalMotors/PositionSensors
  └─ controller_manager  ────────────────────── spawned after 4 s delay
       ├─ joint_state_broadcaster
       └─ base_mecanum_controller  ───────────── mecanum_drive_controller
```

---

### Key ROS 2 topics

| Topic | Type | Description |
|---|---|---|
| `/base_mecanum_controller/reference` | `geometry_msgs/TwistStamped` | Velocity command input (Jazzy uses TwistStamped) |
| `/base_mecanum_controller/cmd_vel` | `geometry_msgs/Twist` | Legacy Twist alias (also accepted) |
| `/base_mecanum_controller/odom` | `nav_msgs/Odometry` | Odometry from wheel encoders |
| `/scan_front_left` | `sensor_msgs/LaserScan` | Front-left LiDAR (360°, 8 m range) |
| `/scan_rear_right` | `sensor_msgs/LaserScan` | Rear-right LiDAR (360°, 8 m range) |
| `/joint_states` | `sensor_msgs/JointState` | All wheel joint states |
| `/tf`, `/tf_static` | `tf2_msgs/TFMessage` | Transform tree (odom → base\_link) |

---

### Full simulation stack (`cmexaiii_webots_full.launch.py`)

Adds SLAM, navigation, and the robot state machine on top of the base simulation:

```bash
ros2 launch cmeresearch_simulation cmexaiii_webots_full.launch.py
```

**Start sequence and timing**

```
t = 0 s   Webots + robot_state_publisher + ros2_control (base sim)
t = 6 s   dual_laser_merger  /scan_front_left + /scan_rear_right → /scan_combined
t = 6 s   twist_mux          /cmd_vel → /base_mecanum_controller/cmd_vel
t = 6 s   state machine      sm_robot, nav_status, system_stats
t = 12 s  SLAM Toolbox        online async mapping on /scan_combined
t = 12 s  Nav2 bringup        planner + controller + recovery behaviours
```

**Additional topics (full stack)**

| Topic | Type | Description |
|---|---|---|
| `/scan_combined` | `sensor_msgs/LaserScan` | Merged 360° scan from both LiDARs |
| `/cmd_vel` | `geometry_msgs/Twist` | Nav2 velocity output (goes into twist_mux) |
| `/teleop/cmd_vel` | `geometry_msgs/Twist` | Manual teleop input (highest priority) |
| `/map` | `nav_msgs/OccupancyGrid` | SLAM live map |
| `/robot_state` | `cmeresearch_msgs/RobotState` | State machine output |
| `/nav_status` | `std_msgs/String` | Navigation goal status |
| `/system_stats` | `std_msgs/String` | CPU / memory / temperature (JSON) |

---

### Sending commands manually

In ROS 2 Jazzy the `mecanum_drive_controller` uses **`TwistStamped`** on the
`/reference` topic by default:

```bash
# Move forward at 0.3 m/s
ros2 topic pub --once /base_mecanum_controller/reference \
  geometry_msgs/msg/TwistStamped \
  "{header: {frame_id: ''}, twist: {linear: {x: 0.3}}}"

# Rotate in place
ros2 topic pub --once /base_mecanum_controller/reference \
  geometry_msgs/msg/TwistStamped \
  "{header: {frame_id: ''}, twist: {angular: {z: 0.5}}}"

# Stop
ros2 topic pub --once /base_mecanum_controller/reference \
  geometry_msgs/msg/TwistStamped "{}"
```

---

### World – indoor\_office.wbt

Two-room office layout (14 × 12 m total):

```
  +─────────────┬─────────────+
  │   Room A    │   Room B    │
  │  (lab/open) │  (office)   │
  │             D             │   D = 1.5 m door opening
  │             │             │
  +─────────────┴─────────────+
```

- Outer walls, one internal dividing wall with a 1.5 m door opening
- Scattered `CardboardBox` and `Table` objects as navigation obstacles
- CMEXAIII robot spawned in Room A at (−4, 0, −2) facing north (−Z / ROS +X)

The world file uses EXTERNPROTO URLs pinned to `R2025a` so it opens
correctly without any local asset downloads beyond what Webots R2025a ships.

---

### Architecture notes

**Coordinate frames**

```
Webots  −Z  ←→  ROS +X  (forward)
Webots  −X  ←→  ROS +Y  (left)
Webots  +Y  ←→  ROS +Z  (up)
```

The `webots_ros2_driver` handles this conversion automatically;
RViz / Nav2 see a standard ROS ENU robot frame.

**Mecanum physics**

Webots uses standard cylinder-shaped wheels (no roller-slip physics).
Forward drive and in-place rotation are physically correct.
True lateral (strafing) motion is constrained by ground friction in simulation —
the `mecanum_drive_controller` will still command the correct per-wheel
velocities but the robot will not move sideways.
All navigation, SLAM, and state machine functionality works correctly.

**Reusing the hardware stack**

Because topic names match the real robot, the following nodes can be launched
alongside the simulation without modification:

```bash
# SLAM mapping (in a second terminal, after the sim is running)
ros2 launch cmeresearch_bringup cmexaiii_nav_mapping.launch.py use_sim_time:=true

# State machine
ros2 launch cmeresearch_robot_state sm_robot.launch.py use_sim_time:=true
```

---

---

## Docker

A self-contained image that bundles Webots R2025a, ROS 2 Jazzy, and all
simulation packages. Useful for CI, clean-room testing, or running the sim
on a machine without a local ROS install.

### Build

Run from the **workspace root** (`ros2_ws/`), not from inside the package:

```bash
docker build \
  -f src/cmeresearch_simulation/docker/Dockerfile \
  -t cmeresearch/simulation:latest \
  .
```

The build:
1. Starts from `ros:jazzy-ros-base`
2. Installs Webots R2025a via the Cyberbotics apt repository
3. Installs all ROS 2 apt dependencies (nav2, slam\_toolbox, webots\_ros2, etc.)
4. Clones the other cme-research source packages via `docker/simulation.repos`
5. Runs `rosdep install` and `colcon build`

> **GitHub authentication**: the repos file uses HTTPS URLs so no SSH key is
> needed inside the build context.  If any repo is private, pass a `GITHUB_TOKEN`
> build-arg and adjust the clone step accordingly.

### Run – with display (X11 forwarding)

```bash
# Allow the container to use the host X server
xhost +local:docker

docker run -it --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  cmeresearch/simulation:latest
```

This starts the full stack (`cmexaiii_webots_full.launch.py`) with the Webots
GUI visible on your desktop.

### Run – headless (no display)

The entrypoint automatically starts **Xvfb** (virtual framebuffer) when
`DISPLAY` is not set, so Webots can initialise without a physical monitor:

```bash
docker run -it --rm \
  cmeresearch/simulation:latest \
  ros2 launch cmeresearch_simulation cmexaiii_webots_full.launch.py gui:=false
```

### Run – base simulation only

```bash
docker run -it --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  cmeresearch/simulation:latest \
  ros2 launch cmeresearch_simulation cmexaiii_webots.launch.py
```

### Useful flags

| Flag | Purpose |
|---|---|
| `--network host` | Share the host network (needed if connecting RViz from the host) |
| `-v $(pwd)/maps:/maps` | Mount a host directory to save SLAM maps |
| `-e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` | Switch DDS middleware |

---

### Docker Compose

`docker/docker-compose.yml` splits the simulation into two services that
communicate over the host network via ROS 2 DDS:

| Service | Profile | What it runs |
|---|---|---|
| `webots_sim` | `base`, `full` | Webots + robot driver + ros2\_control |
| `nav_stack` | `full` | laser merger + twist\_mux + SLAM + Nav2 + state machine |
| `rviz` | `rviz` | RViz2 window (combine with any other profile) |

**Full stack with GUI** (run from `ros2_ws/`):

```bash
xhost +local:docker
docker compose -f src/cmeresearch_simulation/docker/docker-compose.yml \
  --profile full up
```

**Headless** (Xvfb starts automatically inside each container):

```bash
WEBOTS_GUI=false \
docker compose -f src/cmeresearch_simulation/docker/docker-compose.yml \
  --profile full up
```

**Base simulation only** (no SLAM / Nav2):

```bash
xhost +local:docker
docker compose -f src/cmeresearch_simulation/docker/docker-compose.yml \
  --profile base up
```

**Environment variables** (set before `docker compose up`):

| Variable | Default | Description |
|---|---|---|
| `DISPLAY` | _(unset)_ | X11 display; unset → Xvfb |
| `WEBOTS_GUI` | `true` | Set `false` for headless Webots |
| `NAV_STARTUP_DELAY` | `10.0` | Extra seconds nav\_stack waits for Webots |
| `ROS_DOMAIN_ID` | `0` | ROS 2 domain (must match on host if connecting) |
| `RMW_IMPLEMENTATION` | `rmw_fastrtps_cpp` | DDS middleware |

---

## Stage Simulation (legacy, ROS 1)

The Stage worlds under `worlds/cmexa/`, `worlds/cmexaiii/`, and `worlds/ash/`
are for ROS 1 (Melodic/Noetic).  Use `scripts/correct_odometry_msg.py` to fix
the `child_frame_id` on Stage odometry messages.

---

## License

GPLv3 — see [LICENSE](LICENSE)

## Contact

- Email: info@cme-robotics.com
- Website: https://cme-robotics.com
