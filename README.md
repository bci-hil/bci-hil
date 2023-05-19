# README

This is the readme file for getting started with EEG real-time processing using BCI-HIL. The repo includes two demos of real-time BCI applications:
*   Motor Imagery
*   Clear by Mind


## BCI-HIL: Brain Computer Interface Human-in-the-Loop Research Framework:

The functionality and contents of this framework is described in the paper 
*An Open-Source Human-in-the-Loop BCI Research Framework: Method and Design*,
by Martin Gemborn Nilsson, Pex Tufvesson, Frida Heskebeck and Mikael Johansson.

The method paper presents an open-source research framework for the next generation of
brain computer interfaces (BCIs). A grand challenge for current BCI research is establishing
efficient methods for reliable online classification of neural activity. We here introduce a
framework for near real-time classification, analysis, and computations to bring the human into
the loop of learning, evaluation, and improvement. This approach enables the potential of
expanding the boundaries of BCI research in both basic science and applied settings.
The BCI-HIL Research Framework homepage at https://bci.lu.se/bci-hil.


## Dependencies:

The BCI-HIL research framework is built using a few differnt programing languages commonly used packages for these languages. Visualizations and graphics are displayed directly in one or several web browsers using HTML and JavaScript. Real-time features are provided by the Python package Timeflux, while signal processing and machine learning functionalities can be either implemented from scratch or fully performed by (or combined with) standard packages from the Python community, such as SciPy and scikit-learn. A central module is keeping track of the dynamics of the stimuli environment and high-level logic for signal processing and machine learning. Communication is enabled via standardized technologies, such as websockets connecting modules, and LSL facilitating the transfer of EEG data and stimuli streams between the modules and associated hardware.

## Hardware:
The BCI-HIL research framework has been tested with a couple of external EEG-hardware devices:
*   The Crown
*   Muse S
*   Smarting MBT


# Motor Imagery Demo

*Also see the separate [README.md](./src/Motor_Imagery/README.md) file in /src/Motor_Imagery/.* 

This example includes a motor imagery (MI) experiment. The experiment consists three main stages:
* **Calibration session:** Here the user is asked to perform specific MI-tasks, generating labeled data, which is saved. 
* **ML-model training:** Here a ML-model is fitted to the saved data (and other avaialable data for the current user/session).
* **Feedback session:** Here the user is freely performing MI (within the set of classes of MI-tasks used for the calibration session(s)) and the fitted model is trying to predict the current intention of the user.  


# Clear by Mind BCI game

*Also see the separate [README.md](./src/Clear_by_Mind/README.md) file in /src/Clear_by_Mind/.* 

This example includes a simple ERP-based BCI-game called Clear by Mind. Playing the game is simple since no calibration is needed and there is only one stage of the game after it is started.

The user is going to be shown silhouettes of different colors of people. Before starting the game the user is placed in front of the Client GUI and is asked to pick a color, yellow, green, blue or red. The user is then instructed to count the number of occurrences of silhouettes of that color. The game is then started and silhouettes of different colors are flashed for the user. Behind the scenes an algorithm in the Calculate module is trying to figure out which color was chosen by the user. The current belief is presented in the Admin GUI, facing away from the user.


# Getting Started

## Install packages with conda: 
Conda is the package manager that comes with Anaconda and Miniconda, used to manage Python environments. Install one of them first or another package manager of your choice.

We've found that the combination of Python 3.9.16 and numpy 1.22.4 works well, and beware this information might already be obsolete. 

To create and activate a virtual environment using conda: 
```
conda create --name ENV_NAME python=3.9 # Create a virtual python 3.9 environment
conda activate ENV_NAME # Activate the environment
``` 

Timeflux depends on a library called hdf5. If not installed on your OS, do so first. On **MacOS** hdf5 can be installed using homebrew with the command ```brew install hdf5```. To use this when installing timeflux, then do: 
```
HDF5_DIR=/opt/homebrew/opt/hdf5 pip install tables==3.7.0
pip install timeflux
```

A list of Python modules needed is provided in ```requirements.txt``` (created using ```pip freeze > requirements.txt```). All version numbers of the dependencies are listed/included here and this file can be used to install a combination of dependencies known to work together.
```
pip install -r requirements.txt
``` 

## Symbolic link for custom Timeflux nodes in the Calculate module: 

In order to use/modify/create the custom Timeflux nodes that are used in the BCI-HIL Calculate module, these files need to be visible to Timeflux. One way of doing this is to create a symbolic link from the Timeflux installation path to the ```src/nodes_dev/``` folder.

On **Linux, using miniconda,** this could look something like this:
```
ln -s ~/PATH/TO/REPO/bci-hil/src/nodes_dev/ ~/miniconda3/envs/ENV_NAME/lib/python3.9/site-packages/timeflux
```
For **Windows**, check out the ```mklink```-command.

On **MacOS, using miniconda**, this could look something like this:
```
ln -s /PATH/TO/REPO/bci-hil/src/nodes_dev/ /opt/homebrew/Caskroom/miniforge/base/envs/ENV_NAME/lib/python3.9/site-packages/timeflux/
```

# Running a session

## Setup your EEG-hardware:

The first step for running a session is to make sure there is an EEG lsl-stream available. This is done differently for different EEG-hardware. For example, using the *Muse S*, this can be done with the [Muse LSL package](https://github.com/alexandrebarachant/muse-lsl) (already intalled in your environment if you used the ```requirements.txt``` to install Python modules). Follow the instruction for your OS and then start the lsl-stream:
```
muselsl stream
```

## Start a demo application:
In each example folder, there is a ```start_session.sh``` shell script to start all BCI-HIL modules for a session. The individual modules can also be started separately (see below). 

## Start BCI-HIL modules individually:

Each module can also be run separately. This is a good way to test the modules in isolation if you develop your own algorithms/functionality and/or need to troubleshoot.

**Run the Client/Admin modules:**

Navigate to the  ```src/APP_NAME/admin/``` folder and open the  ```admin.html``` file. The Client module can be started in an analgous way.

**Run the Engine module:**

First, open a terminal and navigate to the ```engine/``` folder for the application and run ```engine.py```.
```
cd ~/PATH/TP/REPO/bci-hil/src/APP_NAME/engine/ # Navigate to the engine folder.
python engine.py # Run the Engine module.
```

**Run the Calulate module:** 

First, open a terminal navigate to the ```calculate/graphs/``` folder for the application and run ```main_APP_NAME.yaml```
```
cd ~/PATH/TP/REPO/bci-hil/src/APP_NAME/calculate/graphs/ # Navigate to the graphs folder.
timeflux main_APP_NAME.yaml # Run the Calculate module.
```
If you want to run the application with debug information and set some relevant parameters, the following launch command might be useful:
```
timeflux main_APP_NAME.yaml -d -e SESSION="session0001" -e SUBJECT="subject0001"
```

For more info and options see [running a Timeflux application](#running-a-timeflux-application) below.


# Timeflux
The Calculate modules are built with a Python package called Timeflux. Timeflux is probably best introduced by the documentation itself: https://doc.timeflux.io/en/stable/index.html. An overview can also be found in the BCI-HIL paper.

Applications in Timeflux are composed of one or multiple *graphs*, constructed from *nodes* and directed *edges*. Nodes are used to process data while edges define how and in which direction data flows between the nodes within a graph. All processing steps in one graph are executed at the same frequency, the *rate* of the graph. Different graphs can be executed at different rates and communication between graphs is facilitated by a publisher/subscriber system. Timeflux graphs are defined in ```.yaml``` files, for examples see the ```src/APP_NAME/calculate/graphs/```-folder. Here the ```main_APP_NAME.yaml``` is calling the other ```.yaml``` files where the graphs used for the application are defined.

In order to use/modify/create the custom nodes in BCI-HIL, create the symbolic link as described in the [getting started](#getting-started) section above. Then you can easily add/modify Timeflux-nodes in the ```src/nodes_dev/``` folder.

## Running a Timeflux application:

**Run a Timeflux application:**

```
timeflux application_name.yaml
```

**Run timeflux application with parameters:**

There are also options arguments. For a complete list: 
``` 
timeflux --help
```
Some useful options are the ```--debug``` (or simply ```-d```) flag, and passing environment variables to the Timeflux appliction with the ```-e``` flag:

``` 
timeflux application_name.yaml -d -e VARIABLE_NAME_1="variable_1" -e VARIABLE_NAME_1="variable_2"
``` 

Variables that are useful to set when launching the Motor Imagery or Clear by Mind applications are ```SESSION``` and/or ```SUBJECT```.

## Create a visual representation of a Timeflux application:

A graphical representaiton of a Timeflux application can be created from the ```application_name.yaml``` file with the Python ```graphviz``` package:
```
python -m timeflux.helpers.viz application_name.yaml
```


# Pitfalls and troubleshooting

There are numerous ways that the BCI-HIL research framework may or may not perform as intended.
By carefully reading the log output of the Engine, most problems can be understood and corrected.
Below is a list of potential configuration errors and how to handle them.

## Engine debugging:
Read the console output from the Engine program. Debug messages useful for understanding many issues are printed here.

## Client and Admin GUI debugging:
First, make sure to use the Google Chrome web browser for viewing the respective HTML files. The log output of these programs are found in the *Console* tab in the *Tools for Developers* sidebar. Debug messages useful for understanding many issues are printed here.

## Timeflux and Calculate program debugging:
At runtime, Timeflux provide debug messages if the application is launched with the --debug flag.
If things are not working as expected when building or customizing applications in Timeflux,
a natural initial debugging step would be to verify that all data is passed as expected.

## No LSL stream found:
If a wireless EEG hardware device is used, make sure that it is connected to the same wifi network as the computer that runs the Engine program.
Also, make sure that this wifi network allows device-to-device direct communication with no firewall "protecting" devices from each other.
This may be the case in corporate wifi setups. The solution is to setup your own local wifi network using a personal wifi router,
or even running the experiment using a mobile hotspot from a smartphone.
The availability of LSL-streams can also be checked by installing any LSL recorder software, and there make sure that the EEG hardware can be found.

## EEG data loss or jitter:
The Client GUI in the Clear by Mind example brain game is setup to show EEG data with as low latency as possible.
If frequent disruptions are noticed in the stream of incoming EEG data waveforms, the wireless setup might need to be optimized.
To reduce jitter in the EEG stream, use wired communications wherever possible,
and when forced to use wireless communication make sure that there are as few disturbing devices using the same frequency bands as possible.
Regarding Bluetooth, it is a good idea to turn off other Bluetooth devices in closer proximity than 30 meters.
Regarding wifi, a wifi analyzer app on a smartphone can be used to scan for and identify other wifi nets and routers
that may introduce congestion and impair the wireless channel. It is also possible trying to switch to another wifi channel
in the router providing the experiment wifi.

## LSL timestamp units:
Beware that EEG hardware using LSL can have their own interpretation on how to produce timestamps,
especially when it comes to the unit: seconds, milliseconds, or nanoseconds.
The timestamp may also be offset with zero being the boot time of the system, the Unix epoch in 1970 or any other arbitrary offset.

## Cloud computing:
In this framework, we intentionally refrain from referring to any particular commercial cloud services or providers,
and consider "cloud computing" as any remote computer outside of your local network.
Cloud computing services can provide you with virtual machines that support the websocket technology
that we use as communication channel between modules in BCI-HIL.
The deployment, security, and management of cloud-native technology is beyond the scope of this framework.


# License

BCI-HIL is available under the MIT license.


# Author & Contact

Martin Gemborn Nilsson - martin.gemborn_nilsson@control.lth.se
