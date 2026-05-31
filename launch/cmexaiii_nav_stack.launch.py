"""
CMEXAIII navigation stack – runs without Webots.

Intended to be started after cmexaiii_webots.launch.py (or its container)
is already publishing /scan_front_left, /scan_rear_right, and TF.

Starts (with configurable initial delay):
  t + delay +  0 s   dual_laser_merger   /scan_* → /scan_combined
  t + delay +  0 s   twist_mux           /cmd_vel + /teleop/cmd_vel → controller
  t + delay +  0 s   state machine       sm_robot, nav_status, system_stats
  t + delay +  0 s   mqtt_bridge         ROS ↔ MQTT (private_path cmexaiii-001)
  t + delay +  0 s   wheel_feedback      /joint_states → /cmexaiii/<wheel>/feedback
  t + delay +  6 s   SLAM Toolbox        online async on /scan_combined
  t + delay +  6 s   Nav2 bringup
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode


def generate_launch_description():
    sim_share    = get_package_share_directory('cmeresearch_simulation')
    bringup_share = get_package_share_directory('cmeresearch_bringup')
    slam_share   = get_package_share_directory('slam_toolbox')
    nav2_share   = get_package_share_directory('nav2_bringup')

    # ── Arguments ─────────────────────────────────────────────────────────────
    delay_arg = DeclareLaunchArgument(
        'startup_delay', default_value='6.0',
        description='Seconds to wait before starting any node (let Webots settle)'
    )
    delay = LaunchConfiguration('startup_delay')

    # ── dual_laser_merger ─────────────────────────────────────────────────────
    laser_merger = TimerAction(
        period=delay,
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
                            'laser_1_topic':     '/scan_front_left',
                            'laser_2_topic':     '/scan_rear_right',
                            'merged_scan_topic': '/scan_combined',
                            'target_frame':      'base_link',
                            'laser_1_x_offset':  0.0,
                            'laser_1_y_offset':  0.0,
                            'laser_1_yaw_offset': 0.0,
                            'laser_2_x_offset':  0.0,
                            'laser_2_y_offset':  0.0,
                            'laser_2_yaw_offset': 0.0,
                            'tolerance':         0.05,
                            'queue_size':        10,
                            'angle_increment':   0.00436,
                            'scan_time':         0.032,
                            'use_sim_time':      True,
                        }],
                    ),
                ],
                output='screen',
            ),
        ],
    )

    # ── twist_mux ─────────────────────────────────────────────────────────────
    twist_mux = TimerAction(
        period=delay,
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

    # ── State machine ─────────────────────────────────────────────────────────
    state_machine = TimerAction(
        period=delay,
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

    # ── MQTT bridge + wheel-feedback adapter ──────────────────────────────────
    # mqtt_bridge connects to the local mosquitto broker (started by the
    # `webapp` docker-compose profile) and exposes the same topic surface the
    # real robot exports. wheel_feedback synthesises per-wheel
    # TinkerStepperFeedback from /joint_states because Webots has no
    # Tinkerforge bricklets — the production stepper-driver nodes publish
    # those topics on hardware.
    mqtt_chain = TimerAction(
        period=delay,
        actions=[
            Node(
                package='mqtt_bridge',
                executable='mqtt_bridge_node',
                name='mqtt_bridge_node',
                output='screen',
                parameters=[
                    os.path.join(sim_share, 'config', 'cmexaiii', 'mqtt_bridge_sim_params.yaml'),
                    {'use_sim_time': True},
                ],
            ),
            Node(
                package='cmeresearch_simulation',
                executable='joint_states_to_wheel_feedback.py',
                name='joint_states_to_wheel_feedback',
                output='screen',
                parameters=[{'use_sim_time': True}],
            ),
        ],
    )

    # ── SLAM Toolbox ──────────────────────────────────────────────────────────
    slam_toolbox = TimerAction(
        period=float(6.0),  # extra 6 s on top of startup_delay handled below
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

    # ── Nav2 ──────────────────────────────────────────────────────────────────
    nav2 = TimerAction(
        period=float(6.0),
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

    # SLAM and Nav2 fire after the inner TimerAction fires, which itself fires
    # after laser_merger / twist_mux are already running.
    slam_and_nav = TimerAction(
        period=delay,
        actions=[slam_toolbox, nav2],
    )

    return LaunchDescription([
        delay_arg,
        laser_merger,
        twist_mux,
        state_machine,
        mqtt_chain,
        slam_and_nav,
    ])
