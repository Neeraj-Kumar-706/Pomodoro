#!/bin/bash
set -e

# Get correct paths based on platform
if [ "$(uname -s)" = "Darwin" ]; then
    INSTALL_DIR="$HOME/Library/Application Support/PomodoroTimer"
    APP_DIR="/Applications/PomodoroTimer.app"  # Fixed Mac app location
    APP_DESKTOP="$HOME/Desktop/PomodoroTimer.app"
else
    INSTALL_DIR="$HOME/.local/share/PomodoroTimer"
    DESKTOP_ENTRY="$HOME/.local/share/applications/pomodoro-timer.desktop"
fi

# Backup with timestamp and error handling
if [ -d "$INSTALL_DIR" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_DIR="${INSTALL_DIR}_backup_${TIMESTAMP}"
    echo "Creating backup at: $BACKUP_DIR"
    cp -r "$INSTALL_DIR" "$BACKUP_DIR" || { echo "Backup failed"; exit 1; }
fi

# Deactivate venv if active
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

# Remove files with proper checks
for dir in "$INSTALL_DIR/venv" "$INSTALL_DIR" "$APP_DIR" "$APP_DESKTOP"; do
    [ -d "$dir" ] && rm -rf "$dir" && echo "Removed: $dir"
done

# Remove desktop entries
[ -f "$DESKTOP_ENTRY" ] && rm -f "$DESKTOP_ENTRY" && echo "Removed desktop entry"

echo "Uninstallation complete!"
[ -d "$BACKUP_DIR" ] && echo "Backup available at: $BACKUP_DIR"
