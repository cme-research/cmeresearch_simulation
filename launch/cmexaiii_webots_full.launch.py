"""
Full CMEXAIII simulation launch.

Starts (in order):
  1. Webots + robot_state_publisher + ros2_control  (cmexaiii_webots.launch.py)
  2. dual_laser_merger  – merges /scan_front_left + /scan_rear_right → /scan_combined
  3. twist_mux          – routes /cmd_vel (Nav2) and /teleop/cmd_vel → controller
  4. Robot state machine (sm_robot, nav_status, system_stats)
  5. SLAM Toolbox        – online async mapping on /scan_combined
  6. Nav2 bringup        – full navigation stack

All nodes receive use_sim_time:=true.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode


def generate_launch_description():
    sim_share  = get_package_share_directory('cmeresearch_simulation')
    bringup_share = get_package_share_directory('cmeresearch_bringup')
    slam_share = get_package_share_directory('slam_toolbox')
    nav2_share = get_package_share_directory('nav2_bringup')

    # ── Arguments ─────────────────────────────────────────────────────────────
    gui_arg = DeclareLaunchArgument(
        'gui', default_value='true',
        description='Open the Webots 3D window'
    )
    rviz_arg = DeclareLaunchArgument(
        'rviz', default_value='false',
        description='Launch RViz2'
    )

    gui  = LaunchConfiguration('gui')
    rviz = LaunchConfiguration('rviz')

    # ── 1. Webots core simulation ─────────────────────────────────────────────
    # Starts: Webots, Ros2Supervisor, robot_state_publisher,
    #         WebotsController (with controller_manager), joint_state_broadcaster,
    #         base_mecanum_controller.
    webots_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(sim_share, 'launch', 'cmexaiii_webots.launch.py')
        ),
        launch_arguments={
            'gui':          gui,
            'use_sim_time': 'true',
            'rviz':         rviz,
        }.items(),
    )

    # ── 2. Dual laser merger ──────────────────────────────────────────────────
    # Merges /scan_front_left and /scan_rear_right into /scan_combined.
    # Uses TF (provided by robot_state_publisher) to project both scans into
    # the base_link frame before merging.
    # Delayed 6 s to ensure robot_state_publisher and TF are available.
    laser_merger = TimerAction(
        period=6.0,
        actions=[
            ComposableNodeContainer(
                name='laser_merger_container',
                namespace='',
                package='rclcpp_components',
                executable='component_container',
                composable_node_descriptions=[
                    ComposableNode(
                        package='dual_laser_merger',
                        plugin='merger_node::MergerNode',
                        name='dual_laser_merger',
                        parameters=[{
                            'laser_1_topic':  '/scan_front_left',
                            'laser_2_topic':  '/scan_rear_right',
                            'merged_scan_topic': '/scan_combined',
                            'target_frame':   'base_link',
                            'laser_1_x_offset': 0.0,
                            'laser_1_y_offset': 0.0,
                            'laser_1_yaw_offset': 0.0,
                            'laser_2_x_offset': 0.0,
                            'laser_2_y_offset': 0.0,
                            'laser_2_yaw_offset': 0.0,
                            'tolerance':      0.05,
                            'queue_size':     10,
                            'angle_increment': 0.00436,   # ~0.25 deg steps → 1440 pts
                            'scan_time':       0.032,
                            'use_sim_time':    True,
                        }],
                    ),
                ],
                output='screen',
            ),
        ],
    )

    # ── 3. twist_mux ─────────────────────────────────────────────────────────
    # Subscribes to /cmd_vel (Nav2, priority 10) and /teleop/cmd_vel (priority 100).
    # Output remapped to /base_mecanum_controller/cmd_vel.
    twist_mux = TimerAction(
        period=6.0,
        actions=[
            Node(
                package='twist_mux',
                executable='twist_mux',
                name='twist_mux',
                output='screen',
                remappings=[('cmd_vel_out', '/base_mecanum_controller/cmd_vel')],
                parameters=[
                    os.path.join(sim_share, 'config', 'cmexaiii', 'twist_mux_sim.yaml'),
                    {'use_sim_time': True},
                ],
            ),
        ],
    )

    # ── 4. Robot state machine ────────────────────────────────────────────────
    state_machine = TimerAction(
        period=6.0,
        actions=[
            Node(
                package='cmeresearch_robot_state',
                executable='sm_robot_node',
                name='sm_robot',
                output='screen',
                parameters=[{'use_sim_time': True}],
            ),
            Node(
                package='cmeresearch_robot_state',
                executable='nav_status_node',
                name='nav_status',
                output='screen',
                parameters=[{'use_sim_time': True}],
            ),
            Node(
                package='cmeresearch_robot_state',
                executable='system_stats_node',
                name='system_stats',
                output='screen',
                parameters=[{'use_sim_time': True}],
            ),
        ],
    )

    # ── 5. SLAM Toolbox ───────────────────────────────────────────────────────
    # Online async mapping.  Delayed 12 s to let the laser merger warm up and
    # produce a steady /scan_combined stream.
    slam_toolbox = TimerAction(
        period=12.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(slam_share, 'launch', 'online_async_launch.py')
                ),
                launch_arguments={
                    'use_sim_time':     'true',
                    'slam_params_file': os.path.join(
                        sim_share, 'config', 'cmexaiii', 'slam_params_sim.yaml'
                    ),
                }.items(),
            ),
        ],
    )

    # ── 6. Nav2 bringup ───────────────────────────────────────────────────────
    # Full navigation stack (planner, controller, recovery behaviours).
    # Delayed 12 s so that TF and the map are already coming from SLAM Toolbox
    # before Nav2 tries to subscribe.
    nav2 = TimerAction(
        period=12.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(nav2_share, 'launch', 'navigation_launch.py')
                ),
                launch_arguments={
                    'use_sim_time': 'true',
                    'params_file':  os.path.join(
                        bringup_share, 'config', 'cmexaiii', 'nav_params.yaml'
                    ),
                }.items(),
            ),
        ],
    )

    return LaunchDescription([
        gui_arg,
        rviz_arg,
        webots_launch,
        laser_merger,
        twist_mux,
        state_machine,
        slam_toolbox,
        nav2,
    ])
