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

# Backup only settings
if [ -f "$INSTALL_DIR/settings.json" ]; then
    BACKUP_DIR="$HOME/.config/pomodoro_backups"
    mkdir -p "$BACKUP_DIR"
    cp "$INSTALL_DIR/settings.json" "$BACKUP_DIR/settings_$(date +%Y%m%d_%H%M%S).json" || {
        echo "Failed to backup settings"
        exit 1
    }
    echo "Settings backed up to: $BACKUP_DIR"
fi

# Deactivate venv if active
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

# Kill all instances properly
pkill -f "python.*app-v3.py" || true
sleep 1  # Give processes time to exit

# Remove installation
rm -rf "$INSTALL_DIR"

# Remove files with proper checks
for dir in "$APP_DIR" "$APP_DESKTOP"; do
    [ -d "$dir" ] && rm -rf "$dir" && echo "Removed: $dir"
done

# Cleanup desktop integration
if [ "$OS" != "Darwin" ]; then
    rm -f "$DESKTOP_ENTRY"
    update-desktop-database "$HOME/.local/share/applications" || true
fi

echo "Uninstallation complete!"
