import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    RegisterEventHandler,
    TimerAction,
)
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
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
    desc_share = FindPackageShare('cmeresearch_description')

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

    # ── Robot state publisher (full kinematic URDF) ───────────────────────────
    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name='xacro')]),
        ' ',
        PathJoinSubstitution([
            desc_share, 'urdf', 'cmexaiii', 'robot.urdf.xacro'
        ]),
        ' use_mock_hardware:=false',
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
    # Reads cmexaiii_webots.urdf which declares the ros2_control hardware
    # plugin and sensor configuration consumed by webots_ros2_driver.
    webots_urdf_path = os.path.join(sim_share, 'resource', 'cmexaiii_webots.urdf')
    with open(webots_urdf_path, 'r') as f:
        webots_driver_urdf = f.read()

    controllers_yaml = os.path.join(
        sim_share, 'config', 'cmexaiii', 'base_mecanum_controllers.yaml'
    )

    robot_driver = WebotsController(
        robot_name='cmexaiii',
        parameters=[
            {'robot_description': webots_driver_urdf},
            {'use_sim_time': use_sim_time},
            controllers_yaml,
        ],
        respawn=True,
    )

    # ── ros2_control spawners ─────────────────────────────────────────────────
    # Delayed to allow the controller_manager (started inside robot_driver) to
    # come up before we request activation.
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
        parameters=[{'use_sim_time': use_sim_time}],
    )

    mecanum_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'base_mecanum_controller',
            '--controller-manager', '/controller_manager',
        ],
        parameters=[{'use_sim_time': use_sim_time}],
    )

    delayed_spawners = TimerAction(
        period=4.0,
        actions=[joint_state_broadcaster_spawner, mecanum_controller_spawner],
    )

    # ── Optional RViz ─────────────────────────────────────────────────────────
    rviz_config = os.path.join(sim_share, 'config', 'cmexaiii', 'webots_rviz.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config] if os.path.exists(rviz_config) else [],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=LaunchConfiguration('rviz'),
    )

    # ── Shutdown when Webots GUI closes ───────────────────────────────────────
    shutdown_handler = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=webots._ros2_supervisor,
            on_exit=[EmitEvent(event=Shutdown())],
        )
    )

    return LaunchDescription([
        gui_arg,
        use_sim_time_arg,
        rviz_arg,
        webots,
        webots._ros2_supervisor,
        robot_state_publisher,
        robot_driver,
        delayed_spawners,
        shutdown_handler,
    ])
