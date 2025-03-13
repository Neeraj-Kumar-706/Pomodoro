#!/bin/bash

# Get correct installation path
if [ "$(uname -s)" = "Darwin" ]; then
    APP_DIR="$HOME/Library/Application Support/PomodoroTimer"
    VENV_PATH="$APP_DIR/venv"
else
    APP_DIR="$HOME/.local/share/PomodoroTimer"
    VENV_PATH="$APP_DIR/venv"
fi

# Verify installation and environment
if [ ! -d "$APP_DIR" ] || [ ! -d "$VENV_PATH" ]; then
    echo "Error: Installation not found or corrupted."
    echo "Please run the installer again."
    exit 1
fi

# Change to app directory with error handling
cd "$APP_DIR" || { echo "Failed to change directory"; exit 1; }

# Activate virtual environment with error checking
source "$VENV_PATH/bin/activate" || { echo "Failed to activate virtual environment"; exit 1; }

# Run app with proper output handling
if [ "$(uname -s)" = "Darwin" ]; then
    nohup python app-v3.py >/dev/null 2>&1 &
else
    python app-v3.py >/dev/null 2>&1 & disown
fi

deactivate
exit 0


