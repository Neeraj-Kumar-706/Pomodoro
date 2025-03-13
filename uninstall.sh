#!/bin/bash
set -e  # Exit on error

# Enhanced uninstallation with backup
main() {
    OS="$(uname -s)"
    if [ "$OS" = "Darwin" ]; then
        INSTALL_DIR="$HOME/Applications/PomodoroTimer"
        APP_DIR="$HOME/Desktop/PomodoroTimer.app"
    else
        INSTALL_DIR="$HOME/.local/share/PomodoroTimer"
        DESKTOP_ENTRY="$HOME/Desktop/PomodoroTimer.desktop"
    fi

    # Create backup before removing
    if [ -d "$INSTALL_DIR" ]; then
        backup_dir="${INSTALL_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
        echo "Creating backup at: $backup_dir"
        cp -r "$INSTALL_DIR" "$backup_dir"
        
        echo "Removing installation directory..."
        rm -rf "$INSTALL_DIR"
        echo "Removed app files from: $INSTALL_DIR"
    fi

    # Remove OS-specific files
    if [ "$OS" = "Darwin" ]; then
        if [ -d "$APP_DIR" ]; then
            rm -rf "$APP_DIR"
            echo "Removed Mac app bundle"
        fi
    else
        if [ -f "$DESKTOP_ENTRY" ]; then
            rm "$DESKTOP_ENTRY"
            echo "Removed desktop entry"
        fi
    fi

    echo "Uninstallation complete!"
    echo "Backup available at: $backup_dir"
}

# Run with error handling
trap 'echo "Uninstallation failed"; exit 1' ERR
main
