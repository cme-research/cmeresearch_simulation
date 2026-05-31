#!/usr/bin/env python3
# Bridges /joint_states (from joint_state_broadcaster in Webots) into the
# per-wheel TinkerStepperFeedback topics the webapp expects on the real robot.
# In production those topics are published by the stepper-driver nodes reading
# Tinkerforge bricklets; the sim has no bricklets, so we synthesise the same
# message shape from joint_states. Only current_velocity and current_position
# carry real data; input_voltage is held at the nominal 24 V the bricklets
# report and the remaining fields are zero.
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from cmeresearch_msgs.msg import TinkerStepperFeedback


WHEELS = (
    ('front_left',  'front_left_wheel_joint'),
    ('front_right', 'front_right_wheel_joint'),
    ('rear_left',   'rear_left_wheel_joint'),
    ('rear_right',  'rear_right_wheel_joint'),
)
NOMINAL_INPUT_VOLTAGE_MV = 24000


class WheelFeedbackBridge(Node):
    def __init__(self):
        super().__init__('joint_states_to_wheel_feedback')
        self._pubs = {
            wheel: self.create_publisher(
                TinkerStepperFeedback, f'/cmexaiii/{wheel}/feedback', 10
            )
            for wheel, _ in WHEELS
        }
        self._joint_to_wheel = {joint: wheel for wheel, joint in WHEELS}
        self.create_subscription(JointState, '/joint_states', self._on_joint_state, 50)

    def _on_joint_state(self, msg: JointState):
        for idx, name in enumerate(msg.name):
            wheel = self._joint_to_wheel.get(name)
            if wheel is None:
                continue
            fb = TinkerStepperFeedback()
            fb.header.stamp = msg.header.stamp
            fb.header.frame_id = name
            fb.current_velocity = float(msg.velocity[idx]) if idx < len(msg.velocity) else 0.0
            # current_position is an int32; joint_states position is float radians.
            # The webapp only displays it as a relative count, so a millirad-rounded
            # integer is plenty.
            position = msg.position[idx] if idx < len(msg.position) else 0.0
            fb.current_position = int(round(position * 1000.0))
            fb.remaining_steps = 0
            fb.input_voltage = NOMINAL_INPUT_VOLTAGE_MV
            fb.current_consumption = 0
            self._pubs[wheel].publish(fb)


def main():
    rclpy.init()
    node = WheelFeedbackBridge()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
