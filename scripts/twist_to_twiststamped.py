import rospy
from geometry_msgs.msg import Twist, TwistStamped

class TwistStampedPublisherImpl:
    def __init__(self):
        rospy.Subscriber("/cmd_vel", Twist, self.cmd_msg_receiver_cb)
        self.twist_stamped_pub = rospy.Publisher('/cmd_vel_stamped', TwistStamped, queue_size=10)
        self.twist_stamped_msg = TwistStamped()

    def cmd_msg_receiver_cb(self, msg):
        self.twist_stamped_msg.header.stamp = rospy.Time.now()
        self.twist_stamped_msg.header.frame_id = "base_link"
        self.twist_stamped_msg.linear.x = msg.linear.x
        self.twist_stamped_msg.linear.y = msg.linear.y
        self.twist_stamped_msg.angular.z = msg.angular.z
        self.twist_stamped_pub.publish(self.twist_stamped_msg)

class TwistStampedPublisher:
    def __init__(self):
        self.impl = TwistStampedPublisherImpl()

# main loop
if __name__ == "__main__":
    try:
        rospy.init_node('stage_twist_to_twiststamped_publisher')
        twist_pub = TwistStampedPublisher()
        rospy.spin()

    except rospy.ROSInterruptException:
        pass