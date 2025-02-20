# Robotic Arm

A robotic arm controlled using computer vision.

## Requirements

### Hardware Assembly

- the robotic arm 3d print source files

![Circuit Diagram](./Schematic/schematic.svg)
![On a breadboard](./Schematic/breadboard.svg)

### On the controlling device 

Install the bleak module on the host machine,

This should do.
But for a more reproducible development environment use the devshell provided in flake.nix.
```shell
pip install bleak
pip install numpy
pip install mediapipe
```

Make sure you have tkinter installed.
Run controller.py, it will first connect to the arm then open an interface to control it from.
Run ./handtracking/hand-controller.py
(make sure your working directory is ./handtracking so the script can find the .task file)

### On the arduino

Compile and upload the arduino.ino sketch

## Licenses

[License](./LICENSE.md)
The hand_landmarker task is licensed under Apache License Version 2.0
