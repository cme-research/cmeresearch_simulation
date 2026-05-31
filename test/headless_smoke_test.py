#!/usr/bin/env python3
"""Headless smoke test for the CMEXAIII Webots simulation.

Run inside the simulation Docker container after launching the base sim
(``cmexaiii_webots.launch.py gui:=false``). The test:

  1. Waits up to 120 s for ``/joint_states`` (joint_state_broadcaster active)
     and ``/base_mecanum_controller/odometry`` (mecanum controller spawned
     and Webots ticking) to deliver at least 5 messages each.
  2. Publishes ``TwistStamped(linear.x=0.3)`` on
     ``/base_mecanum_controller/cmd_vel`` for 3 seconds.
  3. Verifies the odometry pose moved at least 5 cm.

Exit code 0 = pass, 1 = fail. Used by the headless-smoke-test CI job.
"""
import sys
import time

import rclpy
from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import JointState

TOPIC_TIMEOUT_S = 120.0
DRIVE_DURATION_S = 3.0
SETTLE_S = 1.0
MIN_DISPLACEMENT_M = 0.05
LINEAR_X = 0.3


class SmokeTest(Node):
    def __init__(self):
        super().__init__('headless_smoke_test')
        self.joint_states = 0
        self.odom_samples = []
        self.create_subscription(JointState, '/joint_states', self._on_js, 10)
        self.create_subscription(
            Odometry, '/base_mecanum_controller/odometry', self._on_odom, 10,
        )
        self.cmd_pub = self.create_publisher(
            TwistStamped, '/base_mecanum_controller/cmd_vel', 10,
        )

    def _on_js(self, msg):
        self.joint_states += 1

    def _on_odom(self, msg):
        p = msg.pose.pose.position
        self.odom_samples.append((p.x, p.y))


def _wait_for_topics(node):
    deadline = time.time() + TOPIC_TIMEOUT_S
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
        if node.joint_states >= 5 and len(node.odom_samples) >= 5:
            return True
        if int(time.time()) % 10 == 0:
            node.get_logger().info(
                f'waiting… joint_states={node.joint_states} '
                f'odom={len(node.odom_samples)}',
                throttle_duration_sec=5.0,
            )
    return False


def _drive_and_measure(node):
    start = node.odom_samples[-1]
    node.get_logger().info(f'topics alive, start pose=({start[0]:.3f}, {start[1]:.3f})')

    end = time.time() + DRIVE_DURATION_S
    while time.time() < end:
        cmd = TwistStamped()
        cmd.header.stamp = node.get_clock().now().to_msg()
        cmd.twist.linear.x = LINEAR_X
        node.cmd_pub.publish(cmd)
        rclpy.spin_once(node, timeout_sec=0.05)

    end = time.time() + SETTLE_S
    while time.time() < end:
        rclpy.spin_once(node, timeout_sec=0.05)

    final = node.odom_samples[-1]
    dx, dy = final[0] - start[0], final[1] - start[1]
    dist = (dx * dx + dy * dy) ** 0.5
    node.get_logger().info(
        f'final pose=({final[0]:.3f}, {final[1]:.3f}) '
        f'Δ=({dx:+.3f}, {dy:+.3f}) dist={dist:.3f} m'
    )
    return dist


def main():
    rclpy.init()
    node = SmokeTest()
    try:
        if not _wait_for_topics(node):
            node.get_logger().error(
                f'FAIL: topics never reached threshold within {TOPIC_TIMEOUT_S:.0f}s '
                f'(joint_states={node.joint_states}, odom={len(node.odom_samples)})'
            )
            return 1
        dist = _drive_and_measure(node)
        if dist < MIN_DISPLACEMENT_M:
            node.get_logger().error(
                f'FAIL: displacement {dist:.3f} m < {MIN_DISPLACEMENT_M:.3f} m — '
                f'controller did not drive the robot'
            )
            return 1
        node.get_logger().info('PASS — sim is alive, mecanum chain accepts /cmd_vel')
        return 0
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    sys.exit(main())
