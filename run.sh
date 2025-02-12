#!/bin/bash
# Run the Pomodoro app using this script from your terminal or command prompt if add it ob to your PATH
# you can change this dir to wherever you want
cd /home/neeraj/apps/Pomodoro
#
#cd /mnt/88c49251-2b3d-489c-be49-24b3d296dd4b/project_decdo/Pomodoro
# set path for your environment
source env/bin/activate
# Run the Pomodoro app
#python app.py & disown use pervious version
python app.py > /dev/null 2>&1 & disown # edit 15/01/25 use app.py for better version
# deactivate environment
deactivate
# Close the terminal
exit 


