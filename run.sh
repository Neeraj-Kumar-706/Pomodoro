#!/bin/bash
# Run the Pomodoro app using this script from your terminal or command prompt if add it ob to your PATH
# you can change this dir to wherever you want
cd /mnt/88c49251-2b3d-489c-be49-24b3d296dd4b/project_decdo/Pomodoro
# set path for your environment
source .venv/bin/activate
# Run the Pomodoro app
python app.py & disown # use app.py for better version
# deactivate environment
deactivate
# Close the terminal
exit 


