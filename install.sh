#!/bin/bash
set -e  # Exit on error

# Check required commands
check_requirements() {
    local missing_deps=()
    for cmd in python3 pip3 bc; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo "Error: Missing required dependencies: ${missing_deps[*]}"
        return 1
    fi
    return 0
}

# Enhanced Python version check
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo "Python 3 is not installed"
        return 1
    fi
    
    # Get major and minor version numbers
    major=$(python3 -c 'import sys; print(sys.version_info.major)')
    minor=$(python3 -c 'import sys; print(sys.version_info.minor)')
    
    # Simple numeric comparison
    if [ "$major" -gt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -ge 8 ]); then
        return 0  # Version is good
    else
        echo "Python 3.8 or higher is required (found ${major}.${minor})"
        return 1
    fi
}

# Backup existing installation
backup_existing() {
    local backup_dir="${1}_backup_$(date +%Y%m%d_%H%M%S)"
    if [ -d "$1" ]; then
        echo "Backing up existing installation..."
        mv "$1" "$backup_dir"
    fi
}

# Main installation
main() {
    if ! check_requirements; then
        exit 1
    fi

    if ! check_python; then
        exit 1
    fi

    # Detect OS
    OS="$(uname -s)"
    if [ "$OS" = "Darwin" ]; then
        INSTALL_DIR="$HOME/Library/Application Support/PomodoroTimer"  # Proper Mac app location
        APP_DIR="/Applications/PomodoroTimer.app"  # Standard Mac app location
        PYTHON_CMD="python3"
        
        # Create Mac app structure
        CONTENTS_DIR="$APP_DIR/Contents"
        MACOS_DIR="$CONTENTS_DIR/MacOS"
        RESOURCES_DIR="$CONTENTS_DIR/Resources"
        
        # Create app bundle directories
        mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"
        
        # Create Info.plist
        cat > "$CONTENTS_DIR/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>PomodoroTimer</string>
    <key>CFBundleIdentifier</key>
    <string>com.pomodoro.timer</string>
    <key>CFBundleName</key>
    <string>PomodoroTimer</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>LSBackgroundOnly</key>
    <string>0</string>
</dict>
</plist>
EOF
        
        # Create launcher script
        cat > "$MACOS_DIR/PomodoroTimer" << EOF
#!/bin/bash
cd "\$(dirname "\$0")"
source "../Resources/venv/bin/activate"
$PYTHON_CMD "../Resources/app-v3.py"
EOF
        chmod +x "$MACOS_DIR/PomodoroTimer"
        
    else
        # Linux setup
        INSTALL_DIR="$HOME/.local/share/PomodoroTimer"
        PYTHON_CMD="python3"
        
        # Create XDG directories if they don't exist
        mkdir -p "$HOME/.local/share/applications"
        
        # Create Linux desktop entry with direct execution
        cat > "$HOME/.local/share/applications/pomodoro-timer.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Pomodoro Timer
GenericName=Pomodoro Timer
Comment=Productivity Timer Application
Exec=sh -c "cd $INSTALL_DIR && . venv/bin/activate && python app-v3.py"
Icon=$INSTALL_DIR/assets/time-organization.png
Terminal=false
Categories=Utility;Office;
Keywords=timer;pomodoro;productivity;
StartupNotify=true
EOF

        chmod +x "$HOME/.local/share/applications/pomodoro-timer.desktop"
        
        # Force desktop database update
        if command -v update-desktop-database >/dev/null 2>&1; then
            update-desktop-database "$HOME/.local/share/applications"
        fi
        if command -v xdg-desktop-menu >/dev/null 2>&1; then
            xdg-desktop-menu forceupdate
        fi
    fi

    # Verify source files exist
    if [ ! -f "draft.py" ] || [ ! -d "assets" ]; then
        echo "Error: Required files not found. Make sure you're in the correct directory."
        exit 1
    fi

    # Store source directory
    SOURCE_DIR="$(pwd)"

    # Create installation directory
    backup_existing "$INSTALL_DIR"
    mkdir -p "$INSTALL_DIR" || { echo "Failed to create installation directory"; exit 1; }

    # Create and activate virtual environment in app directory
    echo "Creating virtual environment..."
    cd "$INSTALL_DIR" || exit 1
    $PYTHON_CMD -m venv venv
    source "venv/bin/activate"

    # Install dependencies from requirements.txt
    echo "Installing dependencies..."
    if [ -f "$SOURCE_DIR/requirements.txt" ]; then
        pip install -r "$SOURCE_DIR/requirements.txt"
    else
        pip install ttkbootstrap pygame matplotlib chime
    fi

    # Copy files with error checking
    echo "Copying application files..."
    if [ "$OS" = "Darwin" ]; then
        cp "$SOURCE_DIR/draft.py" "$RESOURCES_DIR/app-v3.py" || exit 1
        cp -r "$SOURCE_DIR/assets" "$RESOURCES_DIR/" || exit 1
        chmod -R 755 "$APP_DIR" || exit 1
    else
        cp "$SOURCE_DIR/draft.py" "$INSTALL_DIR/app-v3.py" || exit 1
        cp -r "$SOURCE_DIR/assets" "$INSTALL_DIR/" || exit 1
        chmod -R 755 "$INSTALL_DIR" || exit 1
    fi

    # Create initial settings.json
    cat > "$INSTALL_DIR/settings.json" << EOF
{
    "pomodoro": 25,
    "short_break": 5,
    "long_break": 15,
    "mega_goal": 4,
    "auto_switch": true,
    "sound_enabled": true,
    "rain_sound_path": ""
}
EOF

    # Create run script
    if [ "$OS" = "Darwin" ]; then
        cat > "$MACOS_DIR/PomodoroTimer" << EOF
#!/bin/bash
cd "\$(dirname "\$0")"
source "../Resources/venv/bin/activate"
$PYTHON_CMD "../Resources/draft.py"
EOF
    else
        # Create run script for Linux with proper shebang and env activation
        cat > "$INSTALL_DIR/run.sh" << EOF
#!/bin/bash
cd "\$(dirname "\$0")"
source "./venv/bin/activate"
exec python app-v3.py
EOF
        chmod +x "$INSTALL_DIR/run.sh"
        
        # Update desktop entry
        sed -i "s|Exec=.*|Exec=$INSTALL_DIR/run.sh|" "$HOME/.local/share/applications/pomodoro-timer.desktop"
    fi

    echo "Installation complete! App installed to: $INSTALL_DIR"
}

# Run main with error trapping
trap 'echo "Installation failed"; exit 1' ERR
main
