
# BCI-HIL research framework start script.
# Suitable for Linux systems using GNOME.

# Please make sure that your Python environment is setup before running this script
# This is done with something like "conda activate your_virtual_environment"

# Also, this script assumes that Google Chrome is setup as your default web browser.

# For debugging and development, you would probably like to start these
# apps and programs separately - giving you better readability and control over
# each sub module.


# Start the Client web app by opening the file in the default web browser
xdg-open client/client.html

# Start the Admin web app by opening the file in the default web browser
xdg-open admin/admin.html

# Start the Engine program
gnome-terminal -- bash -c "cd ./engine/; python engine.py; exec bash;"

# Start the Calculate program
gnome-terminal -- bash -c "cd ./calculate/graphs/; timeflux main_CBM.yaml -d; exec bash;"
