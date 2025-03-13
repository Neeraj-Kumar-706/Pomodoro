#!/bin/bash

# Get the absolute path to the installation directory
if [ "$(uname -s)" = "Darwin" ]; then
    APP_DIR="$HOME/Applications/PomodoroTimer"
else
    APP_DIR="$HOME/.local/share/PomodoroTimer"
fi

# Check if installation exists
if [ ! -d "$APP_DIR" ]; then
    echo "Pomodoro Timer is not installed. Please run the installer first."
    exit 1
fi

# Check virtual environment
if [ ! -d "$APP_DIR/venv" ]; then
    echo "Virtual environment not found. Please reinstall the application."
    exit 1
fi

# Change to app directory
cd "$APP_DIR" || exit 1

# Activate virtual environment and run app
source "venv/bin/activate"

# Run the app in background and disown
python app-v3.py > /dev/null 2>&1 & disown

# Deactivate venv and exit terminal
deactivate
exit 0


