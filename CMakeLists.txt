cmake_minimum_required(VERSION 3.8)
project(cmeresearch_simulation)

find_package(ament_cmake REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

# ── Scripts ───────────────────────────────────────────────────────────────────
install(PROGRAMS
  scripts/correct_odometry_msg.py
  scripts/correct_odometry_msg
  scripts/joint_states_to_wheel_feedback.py
  DESTINATION lib/${PROJECT_NAME}
)

# ── Maps ──────────────────────────────────────────────────────────────────────
install(DIRECTORY
  maps/
  DESTINATION share/${PROJECT_NAME}/maps
)

# ── Robot configs (Stage) ─────────────────────────────────────────────────────
install(DIRECTORY
  robots/
  DESTINATION share/${PROJECT_NAME}/robots
)

# ── Stage worlds ──────────────────────────────────────────────────────────────
install(DIRECTORY
  worlds/ash/
  DESTINATION share/${PROJECT_NAME}/worlds/ash
)
install(DIRECTORY
  worlds/cmexa/
  DESTINATION share/${PROJECT_NAME}/worlds/cmexa
)
install(DIRECTORY
  worlds/cmexaiii/
  DESTINATION share/${PROJECT_NAME}/worlds/cmexaiii
)
install(DIRECTORY
  worlds/cmexamini/
  DESTINATION share/${PROJECT_NAME}/worlds/cmexamini
)

# ── Webots robot driver URDF ──────────────────────────────────────────────────
install(DIRECTORY
  resource/
  DESTINATION share/${PROJECT_NAME}/resource
)

# ── Simulation configs ────────────────────────────────────────────────────────
install(DIRECTORY
  config/
  DESTINATION share/${PROJECT_NAME}/config
)

# ── Launch files ──────────────────────────────────────────────────────────────
install(DIRECTORY
  launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

ament_package()
