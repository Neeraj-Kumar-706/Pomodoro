#!/bin/bash
set -e

# Get the installation path
if [ "$(uname -s)" = "Darwin" ]; then
    INSTALL_DIR="$HOME/Library/Application Support/PomodoroTimer"
    APP_DIR="/Applications/PomodoroTimer.app"
    RESOURCES_DIR="$APP_DIR/Contents/Resources"
    # For Mac, run from the app bundle
    MACOS_DIR="$APP_DIR/Contents/MacOS"
    if [ -x "$MACOS_DIR/PomodoroTimer" ]; then
        exec "$MACOS_DIR/PomodoroTimer"
        exit 0
    fi
    APP_SCRIPT="$RESOURCES_DIR/app-v3.py"
else
    INSTALL_DIR="$HOME/.local/share/PomodoroTimer"
    APP_SCRIPT="$INSTALL_DIR/app-v3.py"
fi

# Verify paths
[ ! -d "$INSTALL_DIR" ] && { echo "Error: App not installed"; exit 1; }
[ ! -d "$INSTALL_DIR/venv" ] && { echo "Error: Virtual environment not found"; exit 1; }
[ ! -f "$APP_SCRIPT" ] && { echo "Error: App script not found"; exit 1; }

# Check for rain sound configuration
RAIN_SOUND_PATH=""
if [ -f "$INSTALL_DIR/rain_sound_path.txt" ]; then
    RAIN_SOUND_PATH=$(cat "$INSTALL_DIR/rain_sound_path.txt")
    [ ! -f "$RAIN_SOUND_PATH" ] && echo "Warning: Configured rain sound file not found"
fi

# Run app
cd "$INSTALL_DIR" || exit 1
source "venv/bin/activate" || exit 1
python app-v3.py > /dev/null 2>&1 & disown

exit 0


