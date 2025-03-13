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
    version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if (( $(echo "$version < 3.8" | bc -l) )); then
        echo "Python 3.8 or higher is required (found $version)"
        return 1
    fi
    return 0
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
        
        # Create Linux desktop entry
        cat > "$HOME/.local/share/applications/pomodoro-timer.desktop" << EOF
[Desktop Entry]
Version=1.0
Name=Pomodoro Timer
Comment=Pomodoro Timer Application
Exec=bash -c 'cd "$INSTALL_DIR" && source venv/bin/activate && python app-v3.py'
Icon=$INSTALL_DIR/assets/time-organization.png
Terminal=false
Type=Application
Categories=Utility;
EOF
        chmod +x "$HOME/.local/share/applications/pomodoro-timer.desktop"
    fi

    # Verify source files exist
    if [ ! -f "app-v3.py" ] || [ ! -d "assets" ]; then
        echo "Error: Required files not found. Make sure you're in the correct directory."
        exit 1
    fi

    # Create installation directory
    backup_existing "$INSTALL_DIR"
    mkdir -p "$INSTALL_DIR" || { echo "Failed to create installation directory"; exit 1; }

    # Create and activate virtual environment
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv "$INSTALL_DIR/venv"
    source "$INSTALL_DIR/venv/bin/activate"

    # Install dependencies from requirements.txt
    echo "Installing dependencies..."
    if [ -f "requirements.txt" ]; then
        pip install --user --no-cache-dir -r requirements.txt
    else
        pip install --user --no-cache-dir ttkbootstrap pygame matplotlib chime
    fi

    # Copy files with error checking
    echo "Copying application files..."
    if [ "$OS" = "Darwin" ]; then
        cp "app-v3.py" "$RESOURCES_DIR/" || exit 1
        cp -r "assets" "$RESOURCES_DIR/" || exit 1
        chmod -R 755 "$APP_DIR" || exit 1
    else
        cp "app-v3.py" "$INSTALL_DIR/" || exit 1
        cp -r "assets" "$INSTALL_DIR/" || exit 1
        chmod -R 755 "$INSTALL_DIR" || exit 1
    fi

    # Create run script
    if [ "$OS" = "Darwin" ]; then
        cat > "$MACOS_DIR/PomodoroTimer" << EOF
#!/bin/bash
cd "\$(dirname "\$0")"
source "../Resources/venv/bin/activate"
$PYTHON_CMD "../Resources/app-v3.py"
EOF
    else
        cat > "$INSTALL_DIR/run.sh" << EOF
#!/bin/bash
cd "\$(dirname "\$0")"
source "./venv/bin/activate"
python app-v3.py
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
