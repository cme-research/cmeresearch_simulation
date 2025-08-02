define laser_scanners ranger
(
  laser_scanner( pose [ 0.0 0.0 0.0 0.0 ])
)

define laser_scanner sensor
(
  fov 359.0
  range [0.1 8.0]
  samples 640
  color_rgba [ 1 1 0 0.5 ]
  size [ 0.102 0.152 0.106 ]
)

define cmexaiii position
(
  pose [ 1.463 0.036 0.0 0.0 ]

  odom_error [0.03 0.03 0.00 0.02]

  size [ 1.100 0.550 0.950 ]
  origin [ 0.0 0.0 0.0 0.0 ]
  gui_nose 1

  # the base shape of ash
  block
  (
    color "gray"
    points 4
    point[0] [0.0 0.0]
    point[1] [0.550 0.0]
    point[2] [0.550 1.1]
    point[3] [0.0 1.1]
    z [0 0.95]
  )

  # kinematics
  drive "omni"

  # spawn sensors
  laser_scanners()
)
