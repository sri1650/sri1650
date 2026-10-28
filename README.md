# Sri Charan Kumba

**Robotics & Mechatronics Software Engineer**  
Birmingham, United Kingdom · MSc in Mechatronics & Intelligent Machines

I develop and validate software for autonomous robots and industrial automation. My engineering projects span **robot navigation, vision-guided manipulation, visual–inertial state estimation, and multi-robot factory orchestration**. I focus on clear software interfaces, predictable failure handling, and evidence from automated tests and reproducible simulation.

## Featured projects

### [Autonomous Microfactory OS](https://github.com/sri1650/autonomous-microfactory-os)
*Multi-robot orchestration · Python · Rust · gRPC · OR-Tools*

A simulated factory software platform combining constrained job scheduling, conflict-aware robot routing, Rust command runtimes, PostgreSQL persistence, distributed tracing, ClickHouse telemetry, and deterministic event replay.

**Verified scope:** 153 Python and 11 Rust tests; three-job end-to-end integration and failure/recovery scenarios using local services and simulation. [Architecture, benchmarks and reproduction steps](https://github.com/sri1650/autonomous-microfactory-os#readme).

### [Visual-Inertial UAV Navigation](https://github.com/sri1650/visual-inertial-uav-navigation)
*State estimation · Modern C++ · OpenCV · PX4 · Gazebo*

A GPS-denied navigation software project with a 15-state error-state EKF, calibrated camera/IMU interfaces, geometric vision, estimator health/recovery logic, and a MAVLink external-vision adapter.

**Verified scope:** 57 Python and 9 C++ tests; PX4/Gazebo SITL completed 5/5 waypoints and demonstrated estimator-loss failsafe behaviour. The SITL mission used **Gazebo ground truth as external-vision input**; camera-derived VIO trajectory accuracy is not yet measured. [Methods and evidence](https://github.com/sri1650/visual-inertial-uav-navigation#readme).

### [ROS 2 Autonomous Warehouse Robot](https://github.com/sri1650/ros2-autonomous-warehouse-robot)
*ROS 2 Jazzy · Nav2 · C++/Python*

Waypoint mission management, navigation interfaces, a LiDAR/IMU-ready robot model, command/sensor supervision, and diagnostics. Application/build tests are in place; full Gazebo/Nav2 end-to-end validation remains a next step.

### [ROS 2 Vision-Guided Manipulator](https://github.com/sri1650/ros2-vision-guided-manipulator)
*ROS 2 Jazzy · MoveIt 2 · RGB-D perception*

3D target projection, manipulation task orchestration, guarded motion planning, and a **plan-only default**. Core software checks are automated; complete simulated pick-and-place execution and physical arm validation remain future integration work.

### [Industrial Servo Motion Control](https://github.com/sri1650/sri1650/tree/industrial-servo-motion-control)
*Modern C++20 · Python · electromechanical modelling · embedded-style control · fault verification*

Portable cascaded position/velocity/current control, motion planning, synthetic motor identification, fault-latched control loops, fake hardware I/O, virtual CiA 402 states and a **localhost-only** Modbus/TCP test interface.

**Verified scope:** 71 Python tests, four native C++ test suites, 12/12 reproducibility stages and host sanitizers. Selected STM32/encoder gearmotor bench hardware is **not yet connected or validated**; all plant and stop-distance results are simulation-only. [Source, engineering evidence and hardware plan](https://github.com/sri1650/sri1650/tree/industrial-servo-motion-control).

## Technical focus

**Robotics and autonomy:** ROS 2, Nav2, MoveIt 2, Gazebo, PX4 SITL, robot navigation, geometric vision, sensor integration, state estimation, and motion planning.  
**Software engineering:** C++, Python, Rust, Linux, Protobuf/gRPC, Docker, Git, CI, and automated unit/integration testing.  
**Robotics systems:** Multi-agent path planning, constraint-based scheduling, OpenCV, PostgreSQL, OpenTelemetry, ClickHouse, fault injection, diagnostics, and deterministic replay.

## Engineering approach

I prefer **measured behaviour over unverified claims**: explicit state and interface contracts, reproducible test scenarios, traceable failures, and clear separation between unit-tested software, simulated integration, and physical hardware validation.

**Career interests:** Robotics Software Engineering · Mechatronics/Controls Software · Industrial Automation · Autonomy & Perception — UK.
