# CME Research Simulation Package

This ROS package provides simulation environments for CME Robotics research robots using the Stage simulator.

## Overview

The cmeresearch_simulation package contains:

* Robot models for CME Robotics platforms (CMEXA and ASH)
* Simulation environments including house and laboratory (laboriii) settings
* Maps for navigation
* Utility scripts for simulation-to-ROS integration

## Robot Models

The package includes the following robot models:

* **CMEXA**: An omnidirectional robot equipped with a 359° laser scanner
* **ASH**: Another robot platform with similar capabilities

## Simulation Environments

Several world configurations are available:

* **House**: A home environment for testing navigation and behaviors
* **LaborIII**: A laboratory environment for testing

## Dependencies

* ROS (Robot Operating System)
* Stage simulator
* nav_msgs
* rospy

## Utilities

The package includes a utility script to correct odometry messages from Stage to be compatible with the ROS navigation stack by ensuring proper frame IDs.

## License

This package is licensed under GPLv3.

## Contact

For more information, please contact:
- Email: info@cme-robotics.com
- Website: https://cme-robotics.com
