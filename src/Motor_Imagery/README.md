# README:

## BCI-HIL: Brain Computer Interface Human-in-the-Loop Research Framework:

The functionality and contents of this framework is described in the paper: 
*An Open-Source Human-in-the-Loop BCI Research Framework: Method and Design*, 
by Martin Gemborn Nilsson, Pex Tufvesson, Frida Heskebeck and Mikael Johansson.


# Motor Imagery Demo

*Please also see the separate [README.md](../../README.md) file for the whole BCI-HIL research framework.*

This example includes a simple motor imagery (MI) experiment. The experiment consists three main stages:
* **Calibration session:** Here the user is asked to perform specific MI-tasks while data is recorded. 
* **ML-model training:** Here a ML-model is fitted to the recorded data (and other available data for the current user/session).
* **Feedback session:** Here the user is freely performing MI (within the set of classes of MI-tasks used for the calibration session) and a the fitted model is trying to predict the intention of the user.  

If data has already been collected it is also possible to directly fit a ML-model on this data and go directly to the feedback session.


## Buttons: 

In the Admin GUI there are a number of buttons used to control the MI-experiment. Their functionality is described below:

* **Set user number:** Set the user number to the current number in the user no. input field.
* **start calibration:** Set the user number to the current number in the user no. input field and start a calibration run.
* **end calibration:** Stops the calibration and fit model using all available data from the current user and session
* **cancel calibration:** All data since last "Start calibration" will be discarded. Click if something goes wrong during the current run.
* **Start fitting:** Fit model using all available data from the current user and session. When ready the Calculate module transitions to inference mode using the fitted model.
* **Start accumulation:** Epochs, if available will be saved to disk in the Calculate module (i f labels are attached depends on the context). Pressing "Start calibration" automatically enables this behaviour.

Additionally there are buttons for EEG vs. display and audio latency calibration. For audio latency calibration, first click the **Enable audio** button in the *Client GUI*.


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
