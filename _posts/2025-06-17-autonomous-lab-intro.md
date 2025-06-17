---
title: A guide to the BatteryLab project
author: yuanjian
date: 2025-06-17 08:54:00 +0800
categories: [Tutorial]
tags: [Autonomous Laboratory, BatteryLab]
pin: true
---

[BatteryLab](https://github.com/legendPerceptor/BatteryLab) is a project I developed during my Ph.D. fourth year that aims at using robotic arms, a linear rail, and 3D printed parts to autonomously build CR2032 coin cell batteries. I designed the whole lab in [Autodesk Fusion 360](https://www.autodesk.com/products/fusion-360/personal), and developped the robot control programs based on ROS 2 and APIs provided by the manufacturers. Figure 1 shows an overview of the BatteryLab rendered in Fusion 360.

![BatteryLab Overview](https://github.com/legendPerceptor/BatteryLab/raw/main/figures/LabOverview.png)
_Figure 1. An overview of the BatteryLab._

There are 3 Raspberry Pis in the system, each of which controls different parts of the laboratory. The first one (referred to as **R1**) is attached to the Meca500 robotic arm on the linear rail. The second one (referred to as **R2**) is fixed on the breadboard next to the liquid handling robot Dobot MG400. And the third one (referred to as **R3**) is outside the two breadboards that allows users to connect a keyboard, a mouse, and a monitor to give inputs to the system.

> You do not need to connect the input devices or monitor to the Raspberry Pi if you use your laptop to send commands. The whole system can be accessed via wireless network. When put into production, the whole lab can be isolated in a glovebox (power cables need to go through the special port on the glovebox).
{: .prompt-tip }

`BatteryLab` folder contains code that controls each robot without ROS 2. It is a good practice to start with programs in this folder to ensure the hardwares are connected properly, and each robot is functional. We provide an `app.py` file in the root folder that runs separate commands only using the code in `BatteryLab` folder to avoid complication involving ROS 2 and communications. To run this properly, you need to ssh into the proper Rapberry Pi that has a physical connection to the robot to run the commands. For example, if you are in **R1** that connects to the Meca500 on the linear rail while trying to run `breadboard_meca500_example_app()`, you will get an error because only **R2** connects to the liquid handling robot and has access to the comands in the example app. Note that this inconvenience only exists when you want to separately test each robot without using ROS 2. We use ROS 2's communication capabilities to connect all the robots together and when you fully launch our system, you can use any computers to control any robot via wireless network.

> If any robot failed to connect or malfunctioned during the above test stage, you need to dig into the manufacturer's manual to debug each robot separately, because these errors are isolated to our system. Common problems can be IP address mismatch, network issues, robots in an error state, emergency stop button not reset, etc. Please make sure you switch on every hardware button and reset the emergency stop buttons before running any programs.
{: .prompt-warning }

Once you made sure each robot can run separate commands properly, you can move on to launch the BatteryLab via ROS 2. We provided 3 launch files for the 3 Raspberry Pis. They are based on how you connect the cables, and each Raspberry Pi is interchangeble. We used a Raspberry Pi 4 for **R1** and 2 Raspberri Pi 5 for **R2, R3**. The system could run more smoothly if you upgrade all of them to Raspberry Pi 5 or future types of devices. If you use our provided system, the ROS 2 is already set up properly and you can directly launch the system by the following commands.

```bash
# Log in to R3 via ssh or use the keyboard, mouse, and monitor to directly access it
# on R3
ros2 launch battery_lab_bringup/out_rasp.launch.py
```

> I recommend using the Terminator app to have multiple split windows to work with multiple ssh sessions. Some people may like to use `tmux`, which is also fine, but note that you cannot use intuitive mouse drag to select and copy things from a tmux session.
{: .prompt-tip }

```bash
# Use a separate window to ssh into R1, I named R1 "rasp4" in the ssh config, but please double check the ssh config under ~/.ssh/config
ssh rasp4
# on R1
ros2 launch battery_lab_bringup/rail_rasp.launch.py

# Use a separate window to ssh into R2, I named R2 "rasp5" in the ssh config, but please double check the ssh config under ~/.ssh/config
ssh rasp5
# on R2
ros2 launch battery_lab_bringup/board_rasp.launch.py
```

These launch files provide services that you can call later from any computers in the local network. We use these services to control the robots. Then we can start the app from any computers to control the system. You do need to install ROS 2 and the BatteryLab repo properly to run the following command.

```bash
ros2 run assembly_robot app
```

It should be quite intuitive once you sucessfully run the app. Follow the instructions to control the BatteryLab. Check the [readme](https://github.com/legendPerceptor/BatteryLab/blob/main/README.md) for other issues related to compiling and building the project. All the ROS 2 related code is under `ros2_ws/src` folder. Each robot has a separate folder. The `assembly_robot` folder contains control code for the 3 major robotic arms: Liquid Robot (Dobot MG400 + Satorius dispensing module), Crimper Robot (Meca500), Assembly Robot(Meca500 + Zaber Linear Rail). The components like suction pump, camera service, sartorius all have separate folders, and they will be used by the 3 major robotic arms.

