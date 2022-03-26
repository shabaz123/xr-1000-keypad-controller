# xr-1000-keypad-controller

This repository contains the source code, speech files, PCB Gerber files and circuit diagram for the XR-1000 Keypad Controller.

The XR-1000 Keypad Controller allows the user to type instructions using a 4x4 keypad, with confirmation speech from a built-in loudspeaker. The instructions are sent over a serial UART connection. 

The XR-1000 Keypad Controller can be used with the XR-1000 Motion Control Subsystem (just plug a flat flex cable between the two connectors labelled EXPANSION on the two boards).

The source code is in Python and easily adaptable for other purposes, i.e. this project does not have to be used with the XR-1000 Motion Control Subsystem board.

To program the Pi Pico microcontroller used in this project, first go to the CircuitPython website and download CircuitPython for the Pi Pico. Follow the instructions at the CircuitPython website to transfer it to the Pi Pico.

Next, go to the python_code folder in this repository. Copy all the files and paste them into the CircuitPython drive letter that will appear when the Pi Pico is plugged into the PC. That's it, the code is then installed within a minute or so, and the project is ready to go.

