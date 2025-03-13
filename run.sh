#!/bin/bash
set -e

# Get the installation path
if [ "$(uname -s)" = "Darwin" ]; then
    INSTALL_DIR="$HOME/Library/Application Support/PomodoroTimer"
    APP_DIR="/Applications/PomodoroTimer.app"
    # For Mac, run from the app bundle
    MACOS_DIR="$APP_DIR/Contents/MacOS"
    if [ -x "$MACOS_DIR/PomodoroTimer" ]; then
        exec "$MACOS_DIR/PomodoroTimer"
        exit 0
    fi
else
    INSTALL_DIR="$HOME/.local/share/PomodoroTimer"
    # Verify paths
    [ ! -d "$INSTALL_DIR" ] && { echo "Error: App not installed"; exit 1; }
    [ ! -d "$INSTALL_DIR/venv" ] && { echo "Error: Virtual environment not found"; exit 1; }
    [ ! -f "$INSTALL_DIR/draft.py" ] && { echo "Error: App script not found"; exit 1; }

    # Run app
    cd "$INSTALL_DIR" || exit 1
    source "venv/bin/activate" || exit 1
    python draft.py > /dev/null 2>&1 & disown
fi

exit 0


