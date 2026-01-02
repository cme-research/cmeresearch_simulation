cmake_minimum_required(VERSION 3.8)
project(cmeresearch_simulation)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
# uncomment the following section in order to fill in
# further dependencies manually.
find_package(rosidl_default_generators REQUIRED)

if(BUILD_TESTING)
    find_package(ament_lint_auto REQUIRED)
    # the following line skips the linter which checks for copyrights
    # comment the line when a copyright and license is added to all source files
    set(ament_cmake_copyright_FOUND TRUE)
    # the following line skips cpplint (only works in a git repo)
    # comment the line when this package is in a git repo and when
    # a copyright and license is added to all source files
    set(ament_cmake_cpplint_FOUND TRUE)
    ament_lint_auto_find_test_dependencies()
endif()

install(PROGRAMS
    scripts/correct_odometry_msg.py
    scripts/correct_odometry_msg

  DESTINATION lib/${PROJECT_NAME}
)



## Mark other files for installation (e.g. launch and bag files, etc.)
install(FILES
  maps/house/map.pgm
  maps/house/map.png
  maps/house/map.yaml

  DESTINATION share/${PROJECT_NAME}/maps/house/
)

install(FILES
  maps/laboriii/map.pgm
  maps/laboriii/map.png
  maps/laboriii/map.yaml

        DESTINATION share/${PROJECT_NAME}/maps/laboriii/
)

install(FILES
  robots/ash.inc
  robots/cmexa.inc
  robots/cmexaiii.inc

  DESTINATION share/${PROJECT_NAME}/robots/
)

install(FILES
  worlds/ash/house.world

  DESTINATION share/${PROJECT_NAME}/worlds/ash/
)

install(FILES
  worlds/cmexa/house.world
  worlds/cmexa/laboriii.world

  DESTINATION share/${PROJECT_NAME}/worlds/cmexa/
)

install(FILES
  worlds/cmexaiii/laboriii.world

  DESTINATION share/${PROJECT_NAME}/worlds/cmexaiii/
)

install(FILES
  worlds/cmexamini/cmexamini.proto
  worlds/cmexamini/cmexamini.wbt
  worlds/cmexamini/cmexamini2.wbt
  worlds/cmexamini/turtlebot3_burger_example.wbt

  DESTINATION share/${PROJECT_NAME}/worlds/cmexaiii/
)

install(FILES
  launch/cmexaiii_diff.launch

  DESTINATION share/${PROJECT_NAME}/launch/
)
ament_package()
