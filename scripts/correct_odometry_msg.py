import rospy
from nav_msgs.msg import Odometry

class OdometryRepublisherImpl:
    def __init__(self):
        rospy.Subscriber("/odom_in", Odometry, self.odom_msg_receiver_cb)
        self.odom_pub = rospy.Publisher('/odom_out', Odometry, queue_size=10)
        self.odom_msg = Odometry()

    def odom_msg_receiver_cb(self, msg):
        self.odom_msg = msg
        self.odom_msg.child_frame_id = "base_link"
        self.odom_pub.publish(self.odom_msg)

class OdometryRepublisher:
    def __init__(self):
        self.impl = OdometryRepublisherImpl()

# main loop
if __name__ == "__main__":
    try:
        rospy.init_node('stage_odometry_republisher')
        odom_repub = OdometryRepublisher()
        rospy.spin()

    except rospy.ROSInterruptException:
        pass
