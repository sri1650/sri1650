# Hi, I'm Sri 👋

### Robotics & Mechatronics Software Engineer

I build reliable software for autonomous robots and industrial automation — from perception and motion planning to controls, diagnostics, simulation, fleet coordination, state estimation, and CI.

📍 Birmingham, United Kingdom  
🎯 Target roles: Robotics Software Engineer · Mechatronics Software Engineer · Controls Software Engineer · Autonomy / Perception Engineer

## Featured robotics projects

| Project | Engineering focus |
|---|---|
| [**ROS 2 Autonomous Warehouse Robot**](https://github.com/sri1650/ros2-autonomous-warehouse-robot) | ROS 2 Jazzy, C++/Python, Nav2, SLAM, sensor fusion, Gazebo, safety supervision, diagnostics |
| [**ROS 2 Vision-Guided Manipulator**](https://github.com/sri1650/ros2-vision-guided-manipulator) | MoveIt 2, RGB-D perception, 3D pose estimation, guarded arm-motion planning, ros2_control |

## In development

### Autonomous Microfactory OS
Production-style factory robotics software focused on:
- Python orchestration + Rust robot runtime
- multi-robot traffic management and deadlock avoidance
- OR-Tools scheduling and resource allocation
- OpenCV / PyTorch / ONNX inspection
- PostgreSQL + OpenTelemetry + ClickHouse
- deterministic simulation, fault injection, replay, and diagnostic evaluation

### Visual-Inertial UAV Navigation
GPS-denied autonomy project focused on:
- modern C++ visual-inertial navigation foundations
- camera/IMU calibration and timestamp synchronisation
- IMU buffering, bias modelling and preintegration
- OpenCV feature tracking + essential-matrix RANSAC
- estimator TRACKING / DEGRADED / LOST / RESETTING states
- EuRoC-compatible ATE/RPE and fault-injection tooling
- planned PX4 SITL, visual SLAM, embedded Linux, and geo-localisation integration

Both projects keep explicit boundaries between implemented/tested, simulation-validated, and hardware-validated behaviour.

## Technical toolkit

**Robotics:** ROS 2 · Nav2 · MoveIt 2 · Gazebo · SLAM · TF2 · URDF/Xacro · ros2_control · PX4 integration planning  
**Software:** Modern C++ · Python · Rust · Linux · Git · Unit/Integration Testing · GitHub Actions · Docker  
**Autonomy / perception:** Sensor fusion · State estimation · Camera/IMU timing · Geometric vision · Feature tracking · Motion planning  
**Robotics systems:** Fleet coordination · Scheduling · Perception · Diagnostics · Fault recovery · Deterministic replay  
**Data / observability:** PostgreSQL · OpenTelemetry · ClickHouse · structured event logging  
**Supporting skills:** AWS · Kubernetes · Terraform · CI/CD

## Engineering principles

- Clear boundaries between perception, estimation, planning, orchestration, control, and hardware
- Fail-safe defaults, observable health, and explicit degraded/lost states
- Deterministic simulation and tests that produce credible engineering evidence
- Replayable failures rather than “cannot reproduce”
- Measured benchmark evidence instead of unsupported performance claims
- Honest separation between software-complete, simulation-validated, integration-tested, and hardware-validated work

## Current focus

Building a production-grade robotics software portfolio around autonomous mobile robots, vision-guided manipulation, multi-agent factory coordination, visual-inertial navigation, test automation, and observability.
