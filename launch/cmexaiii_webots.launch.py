import os

import launch
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare
from webots_ros2_driver.webots_controller import WebotsController
from webots_ros2_driver.webots_launcher import WebotsLauncher


def generate_launch_description():
    sim_share = get_package_share_directory('cmeresearch_simulation')

    # ── Arguments ─────────────────────────────────────────────────────────────
    gui_arg = DeclareLaunchArgument(
        'gui', default_value='true',
        description='Open the Webots GUI window'
    )
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use Webots simulation clock'
    )
    rviz_arg = DeclareLaunchArgument(
        'rviz', default_value='false',
        description='Launch RViz2 for visualisation'
    )

    use_sim_time = LaunchConfiguration('use_sim_time')

    # ── Webots ────────────────────────────────────────────────────────────────
    world_path = os.path.join(
        sim_share, 'worlds', 'cmexaiii', 'webots', 'indoor_office.wbt'
    )

    webots = WebotsLauncher(
        world=world_path,
        ros2_supervisor=True,
        gui=LaunchConfiguration('gui'),
    )

    # ── Robot state publisher ─────────────────────────────────────────────────
    # Uses a sim-specific xacro that has the same kinematic description as the
    # real robot but replaces the ros2_control hardware plugin with
    # webots_ros2_control::Ros2ControlSystem so the controller_manager (started
    # inside webots_ros2_driver) loads the correct plugin from /robot_description.
    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name='xacro')]),
        ' ',
        PathJoinSubstitution([
            FindPackageShare('cmeresearch_simulation'), 'resource', 'cmexaiii_sim.urdf.xacro'
        ]),
    ])

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[
            {'robot_description': ParameterValue(robot_description_content,
                                                 value_type=str)},
            {'use_sim_time': use_sim_time},
        ],
    )

    # ── Webots robot controller ───────────────────────────────────────────────
    # robot_description points to the webots driver URDF (ros2_control hardware
    # plugin + sensor config), passed as a file path per webots_ros2 convention.
    webots_urdf_path = os.path.join(sim_share, 'resource', 'cmexaiii_webots.urdf')
    controllers_yaml  = os.path.join(
        sim_share, 'config', 'cmexaiii', 'base_mecanum_controllers.yaml'
    )

    robot_driver = WebotsController(
        robot_name='cmexaiii',
        parameters=[
            {'robot_description': webots_urdf_path,
             'use_sim_time': True},
            controllers_yaml,
        ],
        respawn=True,
    )

    # ── ros2_control spawners ─────────────────────────────────────────────────
    # Delayed to give the WebotsController time to connect to Webots and start
    # the controller_manager before we request activation.
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager-timeout', '60'],
    )

    # Remap the controller's input topic from `~/reference` to `~/cmd_vel` so
    # twist_mux's output (cmd_vel_out → /base_mecanum_controller/cmd_vel in the
    # nav_stack launch) reaches the controller. Mirrors what
    # cmeresearch_bringup/launch/cmexaiii_hardware.launch.py does on the real
    # robot — without it the webapp → mqtt → twist_mux chain dead-ends on a
    # topic name mismatch.
    mecanum_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'base_mecanum_controller',
            '--controller-manager-timeout', '60',
            '--controller-ros-args',
            '-r /base_mecanum_controller/reference:=/base_mecanum_controller/cmd_vel',
        ],
    )

    delayed_spawners = TimerAction(
        period=10.0,
        actions=[joint_state_broadcaster_spawner, mecanum_controller_spawner],
    )

    # ── Optional RViz ─────────────────────────────────────────────────────────
    rviz_config = os.path.join(sim_share, 'config', 'cmexaiii', 'webots_rviz.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config] if os.path.exists(rviz_config) else [],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(LaunchConfiguration('rviz')),
    )

    # ── Shutdown when Webots GUI closes ───────────────────────────────────────
    shutdown_handler = launch.actions.RegisterEventHandler(
        event_handler=launch.event_handlers.OnProcessExit(
            target_action=webots,
            on_exit=[launch.actions.EmitEvent(event=launch.events.Shutdown())],
        )
    )

    return LaunchDescription([
        gui_arg,
        use_sim_time_arg,
        rviz_arg,
        webots,
        webots._supervisor,
        robot_state_publisher,
        robot_driver,
        delayed_spawners,
        rviz_node,
        shutdown_handler,
    ])
