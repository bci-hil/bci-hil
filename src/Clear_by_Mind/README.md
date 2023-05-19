# README:

## BCI-HIL: Brain Computer Interface Human-in-the-Loop Research Framework:

The functionality and contents of this framework is described in the paper: 
*An Open-Source Human-in-the-Loop BCI Research Framework: Method and Design*, 
by Martin Gemborn Nilsson, Pex Tufvesson, Frida Heskebeck and Mikael Johansson.


# Clear by Mind

*Please also see the separate [README.md](../../README.md) file for the whole BCI-HIL research framework.*

This example includes a simple ERP-based BCI-game called Clear by Mind. Playing the game is simple since no calibration is needed and there is only one stage of the game after it is started.

The user is going to be shown silhouettes of different colors of people. Before starting the game the user is placed in front of the Client GUI and is asked to pick a color, yellow, green, blue or red. The user is then instructed to count the number of occurrences of silhouettes of that color. The game is then started and silhouettes of different colors are flashed for the user. Behind the scenes an algorithm in the Calculate module is trying to figure out which color was chosen by the user. The current belief is presented in the Admin GUI, facing away from the user.


## Buttons: 

In the Admin GUI there are a number of buttons used to control the MI-experiment. Their functionality is described below:

* **start trial:** Set the user number to the current number in the user no. input field and start a trial of the Clear by Mind game.
* **stop trial:** Stops the current trial and the user game end with the user clicking the correct class category.
* **YELLOW/BLUE/GREEN/RED:** When a trial is over ("stop trial" is clicked), the true category of suspects chosen by the user is clicked. The label information can then be used for offline analysis later on. 
* **cancel trial:** The current trial is aborted and all data saved since "start trial" was clicked will be discarded. Click if something goes wrong during the trial.
* **Start accumulation:** Epochs, if available will be saved to disk in the Calculate module. Pressing "start trial" automatically enables this behaviour.

Additionally there are buttons for going to full screen and EEG vs. display latency calibration.


# License

The MIT License (MIT)

Copyright (c) 2023 Martin Gemborn Nilsson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
